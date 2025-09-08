from asyncio import TimeoutError, sleep
from typing import Any
from xml.etree.ElementTree import ParseError, fromstring

from aiohttp import ClientConnectorError, ContentTypeError

from app.cache import get_cache, set_cache
from app.http_session import get_session
from app.logger import logger
from app.utils.others import looks_like_repo, normalize_repo_url, order_versions
from datetime import datetime


async def get_maven_url_vendor(group_id: str, artifact_id: str, version: str) -> tuple[str, str]:
    session = await get_session()
    url = f"https://repo1.maven.org/maven2/{group_id.replace('.', '/')}/{artifact_id}/{version}/{artifact_id}-{version}.pom"
    while True:
        try:
            logger.info(f"Maven - {url}")
            async with session.get(url) as response:
                response = await response.text()
                break
        except (ClientConnectorError, TimeoutError):
            await sleep(5)
    try:
        session = await get_session()
        pom_url = f"https://repo1.maven.org/maven2/{group_id.replace('.', '/')}/{artifact_id}/{version}/{artifact_id}-{version}.pom"
        async with session.get(pom_url) as pom_response:
            pom_xml = await pom_response.text()
        root = fromstring(pom_xml)
        namespace = {"mvn": "http://maven.apache.org/POM/4.0.0"}
        raw_url = None
        scm_elem = root.find("mvn:scm", namespace)
        if scm_elem is not None:
            url_elem = scm_elem.find("mvn:url", namespace)
            if url_elem is not None:
                raw_url = url_elem.text
            else:
                conn_elem = scm_elem.find("mvn:connection", namespace)
                if conn_elem is not None:
                    raw_url = conn_elem.text
                else:
                    dev_conn_elem = scm_elem.find("mvn:developerConnection", namespace)
                    if dev_conn_elem is not None:
                        raw_url = dev_conn_elem.text
        if not raw_url:
            url_elem = root.find("mvn:url", namespace)
            if url_elem is not None:
                raw_url = url_elem.text
        if raw_url:
            if raw_url.startswith("scm:git:"):
                raw_url = raw_url[8:]
            elif raw_url.startswith("scm:"):
                parts = raw_url.split(":", 2)
                if len(parts) > 2:
                    raw_url = parts[2]
            norm_url = await normalize_repo_url(raw_url)
            if norm_url and await looks_like_repo(norm_url):
                vendor = norm_url.rstrip('/').split('/')[-2]
                return norm_url, vendor
    except ParseError:
        return "", ""
    return "", ""


async def get_maven_versions(group_id: str, artifact_id: str) -> tuple[list[dict[str, Any]], str, str]:
    key = f"{group_id}:{artifact_id}"
    response = await get_cache(key)
    if response:
        versions, repository_url, vendor = response
    else:
        versions: list[dict[str, Any]] = []
        session = await get_session()
        raw_versions: list[dict[str, Any]] = []
        start = 0
        while True:
            url = f"https://search.maven.org/solrsearch/select?q=g:{group_id}+AND+a:{artifact_id}&core=gav&rows=200&start={start}"
            while True:
                try:
                    logger.info(f"Maven - {url}")
                    async with session.get(url) as response:
                        response = await response.json()
                        await set_cache(url, response)
                        break
                except (ClientConnectorError, TimeoutError):
                    await sleep(5)
                except ContentTypeError:
                    return versions, "", ""
            start += 200
            docs = response.get("response", {}).get("docs", [])
            if not docs:
                break
            for doc in docs:
                timestamp_s = doc.get("timestamp") / 1000
                raw_versions.append({
                    "name": doc.get("v"),
                    "release_date": datetime.fromtimestamp(timestamp_s)
                })
        versions = await order_versions("MavenPackage", raw_versions)
        repository_url, vendor = await get_maven_url_vendor(group_id, artifact_id, versions[-1]["name"])
        await set_cache(key, (versions, repository_url, vendor))
    return versions, repository_url, vendor


async def get_maven_version(group_id: str, artifact_id: str, version_name: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    raw_versions: list[dict[str, Any]] = []
    session = await get_session()
    start = 0
    while True:
        url = f"https://search.maven.org/solrsearch/select?q=g:{group_id}+AND+a:{artifact_id}&core=gav&rows=200&start={start}"
        while True:
            try:
                logger.info(f"Maven - {url}")
                async with session.get(url) as response:
                    response = await response.json()
                    break
            except (ClientConnectorError, TimeoutError):
                await sleep(5)
            except ContentTypeError:
                return []
        start += 200
        docs = response.get("response", {}).get("docs", [])
        if not docs:
            break
        for doc in docs:
            raw_versions.append({
                "name": doc.get("v"),
                "release_date": doc.get("timestamp")
            })
    versions = await order_versions("MavenPackage", raw_versions)
    index = next((i for i, d in enumerate(versions) if d.get("name") == version_name), None)
    if index is not None:
        return versions[index], versions[index + 1:]
    else:
        raise ValueError(f"Version {version_name} not found for package {group_id}:{artifact_id}")

async def get_maven_package(group_id: str, artifact_id: str, version_name: str) -> dict[str, Any]:
    key = f"requirement:{group_id}:{artifact_id}:{version_name}"
    response = await get_cache(key)
    if response:
        requirement = response
    else:
        requirement: dict[str, Any] = {}
        session = await get_session()
        url = f"https://repo1.maven.org/maven2/{group_id.replace('.', '/')}/{artifact_id}/{version_name}/{artifact_id}-{version_name}.pom"
        while True:
            try:
                logger.info(f"Maven - {url}")
                async with session.get(url) as response:
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
                if not any(char in dep_version_text for char in ["[", "]", "(", ")"]):
                    dep_version_text = "[" + dep_version_text + "]"
                requirement[f"{dep_group_id}:{dep_artifact_id}"] = dep_version_text
        except ParseError:
            pass
        await set_cache(key, requirement)
    return requirement
