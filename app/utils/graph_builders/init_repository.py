from datetime import datetime
from typing import Any

from pytz import UTC

from app.schemas import InitRepositoryRequest
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
    cargo_create_requirement_file,
    cargo_generate_packages,
    maven_create_requirement_file,
    maven_generate_packages,
    npm_create_requirement_file,
    npm_generate_packages,
    nuget_create_requirement_file,
    nuget_generate_packages,
    pypi_create_requirement_file,
    pypi_generate_packages,
    rubygems_create_requirement_file,
    rubygems_generate_packages,
)


async def init_repository_graph(init_graph_request: InitRepositoryRequest, last_repository_update: dict[str, datetime | bool], last_commit_date: datetime) -> None:
    if last_commit_date is not None and (
        not last_repository_update["moment"]
        or last_repository_update["moment"].replace(tzinfo=UTC)
        < last_commit_date.replace(tzinfo=UTC)
    ):
        repository_id = await read_repositories(
            init_graph_request.owner, init_graph_request.name
        )
        raw_requirement_files = await repo_analyzer(
            init_graph_request.owner, init_graph_request.name
        )
        if not repository_id:
            repository_id = await create_repository(init_graph_request.model_dump())
            await extract_repository(
                raw_requirement_files, repository_id
            )
        else:
            await create_user_repository_rel(
                repository_id, init_graph_request.user_id
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
    await update_repository_users(last_repository_update["id"], init_graph_request.user_id)


async def extract_repository(
    raw_requirement_files: dict[str, Any], repository_id: str
) -> None:
    for name, file in raw_requirement_files.items():
        await select_manager(name, file, repository_id)


async def replace_repository(
    raw_requirement_files: dict[str, Any], repository_id: str
) -> None:
    requirement_files = await read_requirement_files_by_repository(repository_id)
    for file_name, requirement_file_id in requirement_files.items():
        if file_name not in raw_requirement_files:
            await delete_requirement_file(repository_id, file_name)
        else:
            packages = await read_packages_by_requirement_file(requirement_file_id)
            keys = raw_requirement_files[file_name]["requirement"].keys()
            for package_name, constraints in packages.items():
                if package_name in keys:
                    if (
                        constraints
                        != raw_requirement_files[file_name]["requirement"][package_name]
                    ):
                        await update_requirement_rel_constraints(
                            requirement_file_id,
                            package_name,
                            raw_requirement_files[file_name]["requirement"][package_name]
                        )
                else:
                    await delete_requirement_file_rel(
                        requirement_file_id, package_name
                    )
                raw_requirement_files[file_name]["requirement"].pop(package_name)
            if raw_requirement_files[file_name]["requirement"]:
                match raw_requirement_files[file_name]["manager"]:
                    case "PyPI":
                        await pypi_generate_packages(
                            raw_requirement_files[file_name]["requirement"],
                            requirement_file_id,
                        )
                    case "NPM":
                        await npm_generate_packages(
                            raw_requirement_files[file_name]["requirement"],
                            requirement_file_id,
                        )
                    case "Maven":
                        await maven_generate_packages(
                            raw_requirement_files[file_name]["requirement"],
                            requirement_file_id,
                        )
                    case "Cargo":
                        await cargo_generate_packages(
                            raw_requirement_files[file_name]["requirement"],
                            requirement_file_id,
                        )
                    case "NuGet":
                        await nuget_generate_packages(
                            raw_requirement_files[file_name]["requirement"],
                            requirement_file_id,
                        )
                    case "RubyGems":
                        await rubygems_generate_packages(
                            raw_requirement_files[file_name]["requirement"],
                            requirement_file_id,
                        )
                    case _:
                        raise ValueError(
                            f"Unsupported manager: {raw_requirement_files[file_name]['manager']}"
                        )
            await update_requirement_file_moment(requirement_file_id)
        raw_requirement_files.pop(file_name)
    if raw_requirement_files:
        for name, file in raw_requirement_files.items():
            await select_manager(name, file, repository_id)
    await update_repository_moment(repository_id)


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
        case "Cargo":
            await cargo_create_requirement_file(name, file, repository_id)
        case "NuGet":
            await nuget_create_requirement_file(name, file, repository_id)
        case "RubyGems":
            await rubygems_create_requirement_file(name, file, repository_id)
        case _:
            raise ValueError(f"Unsupported manager: {file['manager']}")
