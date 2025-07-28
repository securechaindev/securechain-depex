from typing import Any

from univers.versions import (
    MavenVersion,
    NugetVersion,
    PypiVersion,
    RubygemsVersion,
    SemverVersion,
    Version,
)


async def get_version_type(node_type: str) -> Version:
    return {
        "PyPIPackage": PypiVersion,
        "NPMPackage": SemverVersion,
        "CargoPackage": SemverVersion,
        "MavenPackage": MavenVersion,
        "RubyGemsPackage": RubygemsVersion,
        "NuGetPackage": NugetVersion,
    }.get(node_type, Version)


async def order_versions(node_type: str, raw_versions: list[str]) -> list[dict]:
    version_type: Version = await get_version_type(node_type)
    final_versions: list[dict] = []
    univers_versions: list[tuple[Version, dict[str, Any]]] = []
    for raw_version in raw_versions:
        try:
            univers_versions.append((version_type(raw_version), raw_version))
        except Exception:
            final_versions.append({
                "name": raw_version,
                "serial_number": -1
            })
    univers_versions.sort(key=lambda pair: pair[0])
    for serial_number, (_, raw_version) in enumerate(univers_versions):
        final_versions.append({
            "name": raw_version,
            "serial_number": serial_number
        })
    return final_versions
