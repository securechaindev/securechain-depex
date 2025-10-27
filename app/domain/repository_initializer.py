from datetime import UTC, datetime
from typing import Any

from app.dependencies import ServiceContainer
from app.schemas import PackageMessageSchema
from app.services import (
    PackageService,
    RepositoryService,
    RequirementFileService,
)
from app.utils import ManagerNodeTypeMapper, RedisQueue

from .repo_analyzer import RepositoryAnalyzer


class RepositoryInitializer:
    def __init__(self):
        container = ServiceContainer()
        self.redis_queue: RedisQueue = container.get_redis_queue()
        self.repository_service: RepositoryService = container.get_repository_service()
        self.requirement_file_service: RequirementFileService = container.get_requirement_file_service()
        self.package_service: PackageService = container.get_package_service()
        self.repo_analyzer: RepositoryAnalyzer = RepositoryAnalyzer(container.get_http_session())

    async def init_repository(
        self,
        owner: str,
        name: str,
        user_id: str,
        repository: dict[str, Any] | None,
        last_commit_date: datetime,
    ) -> str:
        raw_requirement_files = await self.repo_analyzer.analyze(owner, name)

        if repository is None:
            repository_data = {
                "owner": owner,
                "name": name,
                "moment": last_commit_date,
                "is_complete": False,
                "user_id": user_id,
            }
            repository_id = await self.repository_service.create_repository(repository_data)

            await self.extract_repository(raw_requirement_files, repository_id)

            await self.repository_service.update_repository_is_complete(repository_id, True)
        else:
            repository_id = repository["id"]

            needs_update = (
                not repository["moment"]
                or repository["moment"].replace(tzinfo=UTC)
                < last_commit_date.replace(tzinfo=UTC)
            )

            if needs_update:
                await self.repository_service.update_repository_is_complete(repository_id, False)

                await self.replace_repository(raw_requirement_files, repository_id)

                await self.repository_service.update_repository_is_complete(repository_id, True)

        await self.repository_service.create_user_repository_rel(repository_id, user_id)

        return repository_id

    async def extract_repository(
        self,
        raw_requirement_files: dict,
        repository_id: str
    ) -> None:
        for name, file_data in raw_requirement_files.items():
            await self.process_requirement_file(name, file_data, repository_id)

    async def replace_repository(
        self,
        raw_requirement_files: dict,
        repository_id: str
    ) -> None:
        existing_files = await self.requirement_file_service.read_requirement_files_by_repository(repository_id)

        for file_name, requirement_file_id in existing_files.items():
            if file_name not in raw_requirement_files:
                await self.requirement_file_service.delete_requirement_file(repository_id, file_name)
            else:
                await self.update_requirement_file(
                    requirement_file_id,
                    raw_requirement_files[file_name],
                )
                raw_requirement_files.pop(file_name)

        if raw_requirement_files:
            for name, file_data in raw_requirement_files.items():
                await self.process_requirement_file(name, file_data, repository_id)

        await self.repository_service.update_repository_moment(repository_id)

    async def update_requirement_file(
        self,
        requirement_file_id: str,
        file_data: dict,
    ) -> None:
        existing_packages = await self.requirement_file_service.read_packages_by_requirement_file(requirement_file_id)
        new_packages = file_data.get("packages", {})

        for package_name, constraints in existing_packages.items():
            if package_name in new_packages:
                if constraints != new_packages[package_name]:
                    await self.requirement_file_service.update_requirement_rel_constraints(
                        requirement_file_id,
                        package_name,
                        new_packages[package_name]
                    )
                new_packages.pop(package_name)
            else:
                await self.requirement_file_service.delete_requirement_file_rel(requirement_file_id, package_name)

        if new_packages:
            manager = file_data.get("manager")
            await self.queue_packages(new_packages, manager, requirement_file_id)

        await self.requirement_file_service.update_requirement_file_moment(requirement_file_id)

    async def process_requirement_file(
        self,
        name: str,
        file_data: dict,
        repository_id: str
    ) -> None:
        manager = file_data.get("manager")
        packages = file_data.get("packages", {})

        req_file_id = await self.create_requirement_file(
            name, manager, repository_id
        )

        await self.queue_packages(packages, manager, req_file_id)

    async def create_requirement_file(
        self,
        name: str,
        manager: str,
        repository_id: str
    ) -> str:
        req_file_dict = {
            "name": name,
            "manager": manager,
            "moment": datetime.now(),
        }
        return await self.requirement_file_service.create_requirement_file(req_file_dict, repository_id)

    async def queue_packages(
        self,
        packages: dict,
        manager: str,
        req_file_id: str
    ) -> None:
        for package_name, constraints in packages.items():
            node_type = self.get_node_type(manager)

            if not await self.package_service.exists_package(node_type, package_name):
                message = PackageMessageSchema(
                    node_type=node_type,
                    package=package_name,
                    vendor="n/a",
                    repository_url=None,
                    constraints=constraints,
                    parent_id=req_file_id,
                    parent_version=None,
                    refresh=False,
                )

                self.redis_queue.add_package_message(message)

    def get_node_type(self, manager: str) -> str:
        return ManagerNodeTypeMapper.manager_to_node_type(manager)
