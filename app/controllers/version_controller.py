from bson import ObjectId

from pkg_resources import parse_version

from app.services.version_service import get_version_by_id

from app.utils.operators import ops


async def filter_versions_db(constraints: list[list[str]], all_versions: list[ObjectId]):
    filter_versions = []

    if 'Any' in constraints:

        filter_versions = all_versions

    else:

        for version_id in all_versions:

            version = await get_version_by_id(version_id)

            checkers = [ops[constraint[0]](parse_version(version['release']), parse_version(constraint[1])) for constraint in constraints]

            if all(checkers): filter_versions.append(version_id)

    return filter_versions