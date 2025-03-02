from asyncio import TimeoutError, sleep
from typing import Any
from xml.etree.ElementTree import ParseError, fromstring

from aiohttp import ClientConnectorError, ClientSession, ContentTypeError

from app.logger import logger


async def get_maven_versions(
    group_id: str, artifact_id: str
) -> list[dict[str, Any]]:
    versions: list[dict[str, Any]] = []
    start = 0
    docs = True
    while docs:
        api_url = f"https://search.maven.org/solrsearch/select?q=g:{group_id}+AND+a:{artifact_id}&core=gav&rows=200&start={start}"
        async with ClientSession() as session:
            while True:
                try:
                    logger.info(f"MAVEN - {api_url}")
                    async with session.get(api_url) as response:
                        response = await response.json()
                        break
                except (ClientConnectorError, TimeoutError):
                    await sleep(5)
                except ContentTypeError:
                    return []
        start += 200
        docs = response.get("response").get("docs", [])
        for count, version in enumerate(response.get("response", {}).get("docs", [])):
            versions.append({"name": version.get("v"), "count": count})
    return versions


async def get_maven_requires(group_id, artifact_id, version):
    require_packages: dict[str, Any] = {}
    api_url = f"https://repo1.maven.org/maven2/{group_id.replace(".", "/")}/{artifact_id}/{version}/{artifact_id}-{version}.pom"
    async with ClientSession() as session:
        while True:
            try:
                logger.info(f"MAVEN - {api_url}")
                async with session.get(api_url) as response:
                    response = await response.text()
                    break
            except (ClientConnectorError, TimeoutError):
                await sleep(5)
    try:
        root = fromstring(response)
        namespace = {"mvn": "http://maven.apache.org/POM/4.0.0"}
        for dep in root.findall(".//mvn:dependency", namespace):
            dep_group_id = dep.find("mvn:groupId", namespace).text
            dep_artifact_id = dep.find("mvn:artifactId", namespace).text
            dep_version = dep.find("mvn:version", namespace)
            dep_version_text = dep_version.text if dep_version is not None else "latest"
            if not any(
                char in dep_version_text for char in ["[", "]", "(", ")"]
            ):
                dep_version_text = "[" + dep_version_text + "]"
            require_packages[
                (dep_group_id, dep_artifact_id)
            ] = dep_version_text
    except ParseError:
        pass
    return require_packages
