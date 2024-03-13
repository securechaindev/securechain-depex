from datetime import datetime
from time import sleep
from typing import Any

from dateutil.parser import parse
from pymongo import ReplaceOne
from requests import ConnectionError, ConnectTimeout, get

from app.config import settings
from app.services import (
    bulk_write_actions,
    read_env_variables,
    update_cpe_products,
    update_env_variables_by_nvd,
)


async def nvd_update() -> None:
    env_variables = await read_env_variables()
    last_update_format = env_variables["nvd_last_update"].isoformat()
    now = datetime.now()
    now_format = datetime.now().isoformat()
    headers = {"apiKey": settings.NVD_API_KEY}
    await update_cves(last_update_format, now_format, headers)
    await update_cpe_matchs(last_update_format, now_format, headers)
    await update_cpes(last_update_format, now_format, headers)
    await update_env_variables_by_nvd(env_variables["_id"], now)


async def update_cves(last_update: str, now: str, headers: dict[str, str]) -> None:
    while True:
        try:
            response = get(
                "https://services.nvd.nist.gov/rest/json/cves/2.0?",
                params={"pubStartDate": last_update, "pubEndDate": now},
                headers=headers,
            ).json()
            break
        except (ConnectTimeout, ConnectionError):
            sleep(5)
    actions = await sanitize_cves(response)
    while True:
        try:
            response = get(
                "https://services.nvd.nist.gov/rest/json/cves/2.0?",
                params={"lastModStartDate": last_update, "lastModEndDate": now},
                headers=headers,
            ).json()
            break
        except (ConnectTimeout, ConnectionError):
            sleep(5)
    actions.extend(await sanitize_cves(response))
    if actions:
        await bulk_write_actions(actions, "cves", True)


async def update_cpe_matchs(
    last_update: str, now: str, headers: dict[str, str]
) -> None:
    while True:
        try:
            response = get(
                "https://services.nvd.nist.gov/rest/json/cpematch/2.0?",
                params={"lastModStartDate": last_update, "lastModEndDate": now},
                headers=headers,
            ).json()
            break
        except (ConnectTimeout, ConnectionError):
            sleep(5)
    actions = await sanitize_cpe_matchs(response)
    if actions:
        await bulk_write_actions(actions, "cpe_matchs", True)


async def update_cpes(last_update: str, now: str, headers: dict[str, str]) -> None:
    while True:
        try:
            response = get(
                "https://services.nvd.nist.gov/rest/json/cpes/2.0?",
                params={"lastModStartDate": last_update, "lastModEndDate": now},
                headers=headers,
            ).json()
            break
        except (ConnectTimeout, ConnectionError):
            sleep(5)
    actions = await sanitize_cpes(response)
    if actions:
        await bulk_write_actions(actions, "cpes", True)


async def sanitize_cves(response: dict[str, Any]) -> list[Any]:
    actions: list[Any] = []
    for cve in response["vulnerabilities"]:
        cve = cve["cve"]
        cve["published"] = parse(cve["published"])
        cve["lastModified"] = parse(cve["lastModified"])
        await get_products(cve)
        actions.append(ReplaceOne({"id": cve["id"]}, cve, upsert=True))
    return actions


async def sanitize_cpe_matchs(response: dict[str, Any]) -> list[Any]:
    actions: list[Any] = []
    for cpe_match in response["matchStrings"]:
        cpe_match = cpe_match["matchString"]
        cpe_match["lastModified"] = parse(cpe_match["lastModified"])
        cpe_match["cpeLastModified"] = parse(cpe_match["cpeLastModified"])
        cpe_match["created"] = parse(cpe_match["created"])
        actions.append(
            ReplaceOne(
                {"matchCriteriaId": cpe_match["matchCriteriaId"]},
                cpe_match,
                upsert=True,
            )
        )
    return actions


async def sanitize_cpes(response: dict[str, Any]) -> list[Any]:
    actions: list[Any] = []
    for cpe in response["products"]:
        cpe = cpe["cpe"]
        cpe["lastModified"] = parse(cpe["lastModified"])
        cpe["created"] = parse(cpe["created"])
        actions.append(ReplaceOne({"cpeNameId": cpe["cpeNameId"]}, cpe, upsert=True))
    return actions


async def get_products(cve: dict[str, Any]) -> None:
    version_keys = (
        "versionStartIncluding",
        "versionEndIncluding",
        "versionStartExcluding",
        "versionEndExcluding",
    )
    if "cvssMetricV31" in cve["metrics"]:
        impact_score = cve["metrics"]["cvssMetricV31"][0]["impactScore"]
    elif "cvssMetricV30" in cve["metrics"]:
        impact_score = cve["metrics"]["cvssMetricV30"][0]["impactScore"]
    elif "cvssMetricV2" in cve["metrics"]:
        impact_score = cve["metrics"]["cvssMetricV2"][0]["impactScore"]
    else:
        impact_score = 0.0
    if "configurations" in cve:
        for configuration in cve["configurations"]:
            for node in configuration["nodes"]:
                if "cpeMatch" in node:
                    for cpe_match in node["cpeMatch"]:
                        cve_ = {
                            "id": cve["id"],
                            "version": cpe_match["criteria"].split(":")[5],
                            "impact_score": impact_score,
                        }
                        if any(key in cpe_match for key in version_keys):
                            if "versionStartIncluding" in cpe_match:
                                cve_["versionStartIncluding"] = cpe_match[
                                    "versionStartIncluding"
                                ]
                            if "versionEndIncluding" in cpe_match:
                                cve_["versionEndIncluding"] = cpe_match[
                                    "versionEndIncluding"
                                ]
                            if "versionStartExcluding" in cpe_match:
                                cve_["versionStartExcluding"] = cpe_match[
                                    "versionStartExcluding"
                                ]
                            if "versionEndExcluding" in cpe_match:
                                cve_["versionEndExcluding"] = cpe_match[
                                    "versionEndExcluding"
                                ]
                        await update_cpe_products(
                            cpe_match["criteria"].split(":")[4], cve_
                        )
                        await update_cpe_products(
                            cpe_match["criteria"].split(":")[3], cve_
                        )
