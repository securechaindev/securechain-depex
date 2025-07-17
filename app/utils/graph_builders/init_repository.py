from datetime import datetime
from typing import Any

from pytz import UTC

from app.services import (
    create_repository,
    create_user_repository_rel,
    delete_requirement_file,
    delete_requirement_file_rel,
    read_packages_by_requirement_file,
    read_repositories,
    read_requirement_files_by_repository,
    update_repository_is_complete,
    update_repository_moment,
    update_repository_users,
    update_requirement_file_moment,
    update_requirement_rel_constraints,
)
from app.utils.repo_analyzer import repo_analyzer
from .managers import (
    maven_create_requirement_file,
    maven_generate_packages,
    cargo_create_requirement_file,
    cargo_generate_packages,
    npm_create_requirement_file,
    npm_generate_packages,
    nuget_create_requirement_file,
    nuget_generate_packages,
    pypi_create_requirement_file,
    pypi_generate_packages,
    rubygems_create_requirement_file,
    rubygems_generate_packages,
)


async def init_repository_graph(repository: dict[str, Any], last_repository_update: dict[str, datetime | bool], last_commit_date: datetime, user_id: str) -> None:
    if last_commit_date is not None and (
        not last_repository_update["moment"]
        or last_repository_update["moment"].replace(tzinfo=UTC)
        < last_commit_date.replace(tzinfo=UTC)
    ):
        repository_id = await read_repositories(
            repository["owner"], repository["name"]
        )
        raw_requirement_files = await repo_analyzer(
            repository["owner"], repository["name"]
        )
        if not repository_id:
            repository_id = await create_repository(repository)
            await extract_repository(
                raw_requirement_files, repository_id
            )
        else:
            await create_user_repository_rel(
                repository_id, user_id
            )
            await update_repository_is_complete(
                repository_id, False
            )
            await replace_repository(
                raw_requirement_files, repository_id
            )
        await update_repository_is_complete(
            repository_id, True
        )
    await update_repository_users(last_repository_update["id"], user_id)


async def extract_repository(
    raw_requirement_files: dict[str, Any], repository_id: str
) -> None:
    for name, file in raw_requirement_files.items():
        await select_manager(name, file, repository_id)


async def replace_repository(
    raw_requirement_files: dict[str, Any], repository_id: str, manager: str
) -> None:
    requirement_files = await read_requirement_files_by_repository(
        repository_id, manager
    )
    for file_name, requirement_file_id in requirement_files.items():
        if file_name not in raw_requirement_files:
            await delete_requirement_file(repository_id, file_name, manager)
        else:
            packages = await read_packages_by_requirement_file(
                requirement_file_id, manager
            )
            keys = raw_requirement_files[file_name]["dependencies"].keys()
            for group_package, constraints in packages.items():
                if manager == "maven":
                    group_id, package = group_package.split(":")
                else:
                    package = group_package
                if package in keys:
                    if (
                        constraints
                        != raw_requirement_files[file_name]["dependencies"][package]
                    ):
                        await update_requirement_rel_constraints(
                            requirement_file_id,
                            package,
                            raw_requirement_files[file_name]["dependencies"][package],
                            manager,
                        )
                else:
                    await delete_requirement_file_rel(
                        requirement_file_id, package, manager
                    )
                if manager == "maven":
                    pop_key = (group_id, package)
                else:
                    pop_key = package
                raw_requirement_files[file_name]["dependencies"].pop(pop_key)
            if raw_requirement_files[file_name]["dependencies"]:
                match manager:
                    case "pypi":
                        await pypi_generate_packages(
                            raw_requirement_files[file_name]["dependencies"],
                            requirement_file_id,
                        )
                    case "npm":
                        await npm_generate_packages(
                            raw_requirement_files[file_name]["dependencies"],
                            requirement_file_id,
                        )
                    case "maven":
                        await maven_generate_packages(
                            raw_requirement_files[file_name]["dependencies"],
                            requirement_file_id,
                        )
            await update_requirement_file_moment(requirement_file_id, manager)
        raw_requirement_files.pop(file_name)
    if raw_requirement_files:
        for name, file in raw_requirement_files.items():
            if file["manager"] == manager:
                await select_manager(manager, name, file, repository_id)
    await update_repository_moment(repository_id, manager)


async def select_manager(
    name: str, file: dict[str, Any], repository_id: str
) -> None:
    match file["manager"]:
        case "PyPI":
            await pypi_create_requirement_file(name, file, repository_id)
        case "NPM":
            await npm_create_requirement_file(name, file, repository_id)
        case "Maven":
            await maven_create_requirement_file(name, file, repository_id)
