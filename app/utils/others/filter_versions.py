from typing import Any

from univers.version_range import (
    CargoVersionRange,
    GemVersionRange,
    MavenVersionRange,
    NpmVersionRange,
    NugetVersionRange,
    PypiVersionRange,
    VersionRange,
)
from univers.versions import (
    MavenVersion,
    NugetVersion,
    PypiVersion,
    RubygemsVersion,
    SemverVersion,
    Version,
)


async def get_version_range_type(node_type: str) -> tuple[Version, VersionRange]:
    return {
        "PyPIPackage": (PypiVersion, PypiVersionRange),
        "NPMPackage": (SemverVersion, NpmVersionRange),
        "CargoPackage": (SemverVersion, CargoVersionRange),
        "MavenPackage": (MavenVersion, MavenVersionRange),
        "RubyGemsPackage": (RubygemsVersion, GemVersionRange),
        "NuGetPackage": (NugetVersion, NugetVersionRange),
    }.get(node_type, (Version, VersionRange))


async def filter_versions(node_type: str, versions: list[dict[str, Any]], constraints: str) -> list[dict[str, Any]]:
    if constraints == "any":
        return versions
    version_type, version_range_type = await get_version_range_type(node_type)
    filtered_versions: list[dict[str, Any]] = []
    try:
        univers_range = version_range_type.from_native(constraints)
        for version in versions:
            univers_version = version_type(version["name"])
            if univers_version in univers_range:
                filtered_versions.append(version)
    except Exception as _:
        return versions
    return filtered_versions
