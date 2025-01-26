from asyncio import TimeoutError, sleep
from typing import Any

from aiohttp import ClientConnectorError, ClientSession
from xmltodict import parse

from app.logger import logger


async def get_all_maven_versions(
    package_artifact_id: str, package_group_id: str
) -> list[dict[str, Any]]:
    versions: list[dict[str, Any]] = []
    async with ClientSession() as session:
        while True:
            try:
                logger.info(f"MAVEN - https://repo1.maven.org/maven2/{package_group_id.replace(".", "/")}/{package_artifact_id}/maven-metadata.xml")
                async with session.get(f"https://repo1.maven.org/maven2/{package_group_id.replace(".", "/")}/{package_artifact_id}/maven-metadata.xml") as response:
                    xml_string = await response.text()
                    break
            except (ClientConnectorError, TimeoutError):
                await sleep(5)
    try:
        pom_dict = parse(xml_string)
    except Exception as _:
        return versions
    if isinstance(pom_dict["metadata"]["versioning"]["versions"]["version"], list):
        raw_versions = pom_dict["metadata"]["versioning"]["versions"]["version"]
    else:
        raw_versions = [pom_dict["metadata"]["versioning"]["versions"]["version"]]
    for count, version in enumerate(raw_versions):
        versions.append({"name": version, "release_date": None, "count": count})
    return versions


async def requires_maven_packages(
    package_artifact_id: str, package_group_id: str, version_dist: str
) -> dict[str, list[str] | str]:
    require_packages: dict[str, Any] = {}
    group_id = package_group_id.replace(".", "/")
    async with ClientSession() as session:
        while True:
            try:
                logger.info(f"MAVEN - https://repo1.maven.org/maven2/{group_id}/{package_artifact_id}/{version_dist}/{package_artifact_id}-{version_dist}.pom")
                async with session.get(f"https://repo1.maven.org/maven2/{group_id}/{package_artifact_id}/{version_dist}/{package_artifact_id}-{version_dist}.pom") as response:
                    xml_string = await response.text()
                    break
            except (ClientConnectorError, TimeoutError):
                await sleep(5)
    try:
        pom_dict = parse(xml_string)
    except Exception as _:
        return require_packages
    if "project" in pom_dict:
        if "dependencyManagement" in pom_dict["project"]:
            if (
                "dependencies" in pom_dict["project"]
                and "dependencies" in pom_dict["project"]["dependencyManagement"]
                and pom_dict["project"]["dependencyManagement"]["dependencies"]
            ):
                if "dependency" in pom_dict["project"]["dependencies"]:
                    if isinstance(
                        pom_dict["project"]["dependencies"]["dependency"], list
                    ) and isinstance(
                        pom_dict["project"]["dependencyManagement"]["dependencies"][
                            "dependency"
                        ],
                        list,
                    ):
                        pom_dict["project"]["dependencies"]["dependency"].extend(
                            pom_dict["project"]["dependencyManagement"]["dependencies"][
                                "dependency"
                            ]
                        )
                    elif isinstance(
                        pom_dict["project"]["dependencies"]["dependency"], list
                    ) and isinstance(
                        pom_dict["project"]["dependencyManagement"]["dependencies"][
                            "dependency"
                        ],
                        dict,
                    ):
                        pom_dict["project"]["dependencies"]["dependency"].append(
                            pom_dict["project"]["dependencyManagement"]["dependencies"][
                                "dependency"
                            ]
                        )
                    elif isinstance(
                        pom_dict["project"]["dependencies"]["dependency"], dict
                    ) and isinstance(
                        pom_dict["project"]["dependencyManagement"]["dependencies"][
                            "dependency"
                        ],
                        list,
                    ):
                        pom_dict["project"]["dependencyManagement"]["dependencies"][
                            "dependency"
                        ].append(pom_dict["project"]["dependencies"]["dependency"])
                        pom_dict["project"]["dependencies"]["dependency"] = pom_dict[
                            "project"
                        ]["dependencyManagement"]["dependencies"]["dependency"]
                    else:
                        pom_dict["project"]["dependencies"]["dependency"] = [
                            pom_dict["project"]["dependencies"]["dependency"],
                            pom_dict["project"]["dependencyManagement"]["dependencies"][
                                "dependency"
                            ],
                        ]
            else:
                pom_dict["project"]["dependencies"] = pom_dict["project"][
                    "dependencyManagement"
                ]["dependencies"]
        if (
            "dependencies" in pom_dict["project"]
            and pom_dict["project"]["dependencies"] is not None
            and "dependency" in pom_dict["project"]["dependencies"]
        ):
            properties = {}
            if (
                "properties" in pom_dict["project"]
                and pom_dict["project"]["properties"]
            ):
                properties.update(pom_dict["project"]["properties"])
            if "parent" in pom_dict["project"] and pom_dict["project"]["parent"]:
                properties.update(pom_dict["project"]["parent"])
            if isinstance(pom_dict["project"]["dependencies"]["dependency"], list):
                dependencies = pom_dict["project"]["dependencies"]["dependency"]
            else:
                dependencies = [pom_dict["project"]["dependencies"]["dependency"]]
            for dependency in dependencies:
                if "scope" not in dependency or dependency["scope"] in (
                    "compile",
                    "runtime",
                    "provided",
                ):
                    version = ""
                    if "version" in dependency and dependency["version"] is not None:
                        version = (
                            pom_dict["project"]["version"]
                            if "$" in dependency["version"]
                            and "project.version" in dependency["version"]
                            and "version" in pom_dict["project"]
                            else dependency["version"]
                        )
                        if "properties" in pom_dict["project"] or not any(
                            "$" in att
                            for att in (
                                dependency["groupId"],
                                dependency["artifactId"],
                                version,
                            )
                        ):
                            if "$" in dependency["groupId"]:
                                property_ = (
                                    dependency["groupId"]
                                    .replace("$", "")
                                    .replace("{", "")
                                    .replace("}", "")
                                )
                                if property_ and property_ in properties:
                                    if isinstance(properties[property_], list):
                                        dependency["groupId"] = properties[property_][0]
                                    else:
                                        dependency["groupId"] = properties[property_]
                                else:
                                    continue
                            if "$" in dependency["artifactId"]:
                                property_ = (
                                    dependency["artifactId"]
                                    .replace("$", "")
                                    .replace("{", "")
                                    .replace("}", "")
                                )
                                if property_ and property_ in properties:
                                    if isinstance(properties[property_], list):
                                        dependency["artifactId"] = properties[
                                            property_
                                        ][0]
                                    else:
                                        dependency["artifactId"] = properties[property_]
                                else:
                                    continue
                            if "$" in version:
                                property_ = (
                                    version.replace("$", "")
                                    .replace("{", "")
                                    .replace("}", "")
                                )
                                if property_ and property_ in properties:
                                    if isinstance(properties[property_], list):
                                        version = properties[property_][0]
                                    else:
                                        version = properties[property_]
                                else:
                                    version = ""
                            if not any(
                                char in version for char in ["[", "]", "(", ")"]
                            ):
                                version = "[" + version + "]"
                    version = version if version else "any"
                    require_packages[
                        (dependency["groupId"], dependency["artifactId"])
                    ] = version
    return require_packages
