from typing import Any, ClassVar

from univers.version_range import (
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


class VersionFilter:
    VERSION_RANGE_MAP: ClassVar[dict[str, tuple[type[Version], type[VersionRange]]]] = {
        "PyPIPackage": (PypiVersion, PypiVersionRange),
        "NPMPackage": (SemverVersion, NpmVersionRange),
        "CargoPackage": (SemverVersion, NpmVersionRange),
        "MavenPackage": (MavenVersion, MavenVersionRange),
        "RubyGemsPackage": (RubygemsVersion, GemVersionRange),
        "NuGetPackage": (NugetVersion, NugetVersionRange),
    }

    @staticmethod
    def get_version_range_type(node_type: str) -> tuple[Version, VersionRange]:
        return VersionFilter.VERSION_RANGE_MAP.get(node_type, (Version, VersionRange))

    @staticmethod
    def filter_versions(node_type: str, versions: list[dict[str, Any]], constraints: str) -> list[dict[str, Any]]:
        if constraints == "any":
            return versions
        version_type, version_range_type = VersionFilter.get_version_range_type(node_type)
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
