from time import sleep
from typing import Any

from requests import ConnectionError, ConnectTimeout, get
from xmltodict import parse


async def get_all_mvn_versions(
    package_artifact_id: str, package_group_id: str
) -> list[dict[str, Any]]:
    versions: list[dict[str, Any]] = []
    while True:
        try:
            response = get(
                f"https://repo1.maven.org/maven2/{package_group_id.replace(".", "/")}/{package_artifact_id}/maven-metadata.xml"
            )
            break
        except (ConnectTimeout, ConnectionError):
            sleep(5)
    xml_string = response.text
    try:
        python_dict = parse(xml_string)
    except Exception as _:
        return versions
    if isinstance(python_dict["metadata"]["versioning"]["versions"]["version"], list):
        raw_versions = python_dict["metadata"]["versioning"]["versions"]["version"]
    else:
        raw_versions = [python_dict["metadata"]["versioning"]["versions"]["version"]]
    for count, version in enumerate(raw_versions):
        versions.append({"name": version, "release_date": None, "count": count})
    return versions


async def requires_mvn_packages(
    package_artifact_id: str, package_group_id: str, version_dist: str
) -> dict[str, list[str] | str]:
    require_packages: dict[str, Any] = {}
    group_id = package_group_id.replace(".", "/")
    while True:
        try:
            response = get(
                f"https://repo1.maven.org/maven2/{group_id}/{package_artifact_id}/{version_dist}/{package_artifact_id}-{version_dist}.pom"
            )
            break
        except (ConnectTimeout, ConnectionError):
            try:
                response = get(
                    f"https://search.maven.org/remotecontent?filepath={group_id}/{package_artifact_id}/{version_dist}/{package_artifact_id}-{version_dist}.pom"
                )
                break
            except (ConnectTimeout, ConnectionError):
                sleep(5)
    xml_string = response.text
    try:
        python_dict = parse(xml_string)
    except Exception as _:
        return require_packages
    if (
        "project" in python_dict
        and "dependencies" in python_dict["project"]
        and python_dict["project"]["dependencies"] is not None
        and "dependency" in python_dict["project"]["dependencies"]
    ):
        if isinstance(python_dict["project"]["dependencies"]["dependency"], list):
            dists = python_dict["project"]["dependencies"]["dependency"]
        else:
            dists = [python_dict["project"]["dependencies"]["dependency"]]
        for dist in dists:
            if "scope" not in dist or dist["scope"] in ("compile", "runtime"):
                version = (
                    dist["version"]
                    if "version" in dist and dist["version"] is not None
                    else "[0.0,)"
                )
                if "properties" in python_dict["project"] or not any(
                    "$" in att for att in (dist["groupId"], dist["artifactId"], version)
                ):
                    if "$" in dist["groupId"]:
                        property_ = (
                            dist["groupId"]
                            .replace("$", "")
                            .replace("{", "")
                            .replace("}", "")
                        )
                        if property_ in python_dict["project"]["properties"]:
                            dist["groupId"] = python_dict["project"]["properties"][
                                property_
                            ]
                        else:
                            continue
                    if "$" in dist["artifactId"]:
                        property_ = (
                            dist["artifactId"]
                            .replace("$", "")
                            .replace("{", "")
                            .replace("}", "")
                        )
                        if property_ in python_dict["project"]["properties"]:
                            dist["artifactId"] = python_dict["project"]["properties"][
                                property_
                            ]
                        else:
                            continue
                    if "$" in version:
                        property_ = (
                            version.replace("$", "").replace("{", "").replace("}", "")
                        )
                        if property_ in python_dict["project"]["properties"]:
                            version = python_dict["project"]["properties"][property_]
                        else:
                            version = "[0.0,)"
                    if not any(char in version for char in ["[", "]", "(", ")"]):
                        version = "[" + version + "]"
                    require_packages[(dist["groupId"], dist["artifactId"])] = version
    return require_packages
