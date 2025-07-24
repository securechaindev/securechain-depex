from typing import Any

from app.apis import (
    get_cargo_version,
    get_maven_version,
    get_npm_version,
    get_nuget_version,
    get_pypi_version,
    get_rubygems_version,
)
from app.schemas import InitVersionRequest
from app.services import create_versions

from .managers import (
    cargo_extract_packages,
    maven_extract_packages,
    npm_generate_packages,
    nuget_generate_packages,
    pypi_extract_packages,
    rubygems_extract_packages,
)

from .managers.vulnerabilities import attribute_vulnerabilities


async def create_version(init_version_request: InitVersionRequest) -> None:
    version, requirements = await get_version(init_version_request)
    attributed_version = await attribute_vulnerabilities(
        init_version_request.node_type.value,
        version
    )
    created_versions = await create_versions(
        init_version_request.node_type.value,
        init_version_request.package_name,
        [attributed_version]
    )
    for version in created_versions:
        match init_version_request.node_type.value:
            case "CargoPackage":
                await cargo_extract_packages(init_version_request.package_name, version)
            case "MavenPackage":
                await maven_extract_packages(init_version_request.package_name, version)
            case "NPMPackage":
                await npm_generate_packages(requirements, version["id"], init_version_request.version_name)
            case "NuGetPackage":
                await nuget_generate_packages(requirements, version["id"], init_version_request.version_name)
            case "PyPIPackage":
                await pypi_extract_packages(init_version_request.package_name, version)
            case "RubyGemsPackage":
                await rubygems_extract_packages(init_version_request.package_name, version)
            case _:
                raise ValueError(f"Unsupported node type: {init_version_request.node_type.value}")


async def get_version(
    init_version_request: InitVersionRequest
) -> dict[str, Any]:
    match init_version_request.node_type.value:
        case "CargoPackage":
            return (await get_cargo_version(
                init_version_request.package_name,
                init_version_request.version_name
            ), None)
        case "NPMPackage":
            return await get_npm_version(
                init_version_request.package_name,
                init_version_request.version_name
            )
        case "NuGetPackage":
            return await get_nuget_version(
                init_version_request.package_name,
                init_version_request.version_name
            )
        case "MavenPackage":
            if ":" not in init_version_request.package_name:
                raise ValueError("Maven package name must be in the format 'group_id:artifact_id'")
            group_id, artifact_id = init_version_request.package_name.split(":")
            return (await get_maven_version(
                group_id,
                artifact_id,
                init_version_request.version_name
            ), None)
        case "PyPIPackage":
            return (await get_pypi_version(
                init_version_request.package_name,
                init_version_request.version_name
            ), None)
        case "RubyGemsPackage":
            return (await get_rubygems_version(
                init_version_request.package_name,
                init_version_request.version_name
            ), None)
        case _:
            raise ValueError(f"Unsupported node type: {init_version_request.node_type.value}")
