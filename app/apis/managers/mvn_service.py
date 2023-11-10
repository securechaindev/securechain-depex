from time import sleep
from typing import Any

from requests import ConnectionError, ConnectTimeout, get
from xmltodict import parse


async def get_all_mvn_versions(pkg_name: str) -> list[dict[str, Any]]:
    parts = pkg_name.split(":")
    pkg_url = parts[0].replace(".", "/") + "/" + parts[1]
    while True:
        try:
            response = get(
                f"https://repo1.maven.org/maven2/{pkg_url}/maven-metadata.xml"
            )
            break
        except (ConnectTimeout, ConnectionError):
            sleep(5)
    xml_string = response.text
    try:
        python_dict = parse(xml_string)
    except Exception as _:
        return []
    if isinstance(python_dict["metadata"]["versioning"]["versions"]["version"], list):
        raw_versions = python_dict["metadata"]["versioning"]["versions"]["version"]
    else:
        raw_versions = [python_dict["metadata"]["versioning"]["versions"]["version"]]
    versions: list[dict[str, Any]] = []
    for count, version in enumerate(raw_versions):
        versions.append({"name": version, "release_date": None, "count": count})
    return versions


async def requires_mvn_packages(
    pkg_name: str, version_dist: str
) -> dict[str, list[str] | str]:
    parts = pkg_name.split(":")
    pkg_url = parts[0].replace(".", "/") + "/" + parts[1]
    while True:
        try:
            response = get(
                f"https://repo1.maven.org/maven2/{pkg_url}/{version_dist}/{parts[1]}-{version_dist}.pom"
            )
            break
        except (ConnectTimeout, ConnectionError):
            sleep(5)
    xml_string = response.text
    try:
        python_dict = parse(xml_string)
    except Exception as _:
        return {}
    if (
        "dependencies" in python_dict["project"]
        and python_dict["project"]["dependencies"] is not None
    ):
        require_packages: dict[str, Any] = {}
        if isinstance(python_dict["project"]["dependencies"]["dependency"], list):
            dists = python_dict["project"]["dependencies"]["dependency"]
        else:
            dists = [python_dict["project"]["dependencies"]["dependency"]]
        for dist in dists:
            if "scope" not in dist or dist["scope"] != "test":
                pkg_name = dist["groupId"] + ":" + dist["artifactId"]
                version = dist["version"] if "version" in dist else "[0.0,)"
                # TODO: Ver como recuperar la info indexada con $
                if "$" in version or "$" in pkg_name:
                    continue
                if not any(char in version for char in ["[", "]", "(", ")"]):
                    version = "[" + version + "]"
                require_packages[pkg_name] = version
        return require_packages
    return {}
