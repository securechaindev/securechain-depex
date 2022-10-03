from bson import ObjectId

from pkg_resources import parse_version

from app.services.version_service import read_version_by_id, update_versions_cves

from app.utils.operators import ops

from copy import copy


async def filter_versions_db(constraints: list[list[str]], all_versions: list[ObjectId]):
    if constraints == 'any':
        return all_versions

    filter_versions = []

    for version_id in all_versions:
        version = await read_version_by_id(version_id)
        checkers = [ops[constraint[0]](parse_version(version['release']), parse_version(constraint[1])) for constraint in constraints]
        if all(checkers): filter_versions.append(version_id)

    return filter_versions

async def update_versions_by_constraints(constraints: list[list[str]], cve_id: ObjectId) -> None:
    query: dict = {}

    if constraints:
        query = {'$and': []}
        for ctc in constraints:
            query['$and'].append(await get_query(ctc))

    await update_versions_cves(query, cve_id)

async def get_query(constraint: list[str]) -> dict:
    version = constraint[1]
    number_of_points = version.count('.')
    number_of_elements = number_of_points + 1
    xyzd = await sanitize(version, number_of_points)

    match constraint[0]:
        case '=' | '==':
            query = await equal_query(xyzd)
        case '<':
            query = await less_than_query(xyzd)
        case '>':
            query = await greater_than_query(xyzd)
        case '>=':
            query = await greater_or_equal_than_query(xyzd)
        case '<=':
            query = await less_or_equal_than_query(xyzd)
        case '!=':
            query = await not_equal_query(xyzd)
        case '^':
            query = await approx_gt_patch(xyzd)
        case '~>' | '~=' | '~':
            query = await approx_gt_minor(xyzd, number_of_elements)

    return query

async def sanitize(version: str, number_of_points: int) -> list[int]:
    match number_of_points:
        case 0:
            version += '.0.0.0'
        case 1:
            version += '.0.0'
        case 2:
            version += '.0'
    return [int(n) for n in version.split('.')]

async def equal_query(xyzd: list[int]) -> dict:
    return {'$and': [
        {'mayor': {'$eq': xyzd[0]}},
        {'minor': {'$eq': xyzd[1]}},
        {'patch': {'$eq': xyzd[2]}},
        {'build_number': {'$eq': xyzd[3]}}
    ]}

async def greater_than_query(xyzd: list[int]) -> dict:
    return {'$or': [
        {'mayor': {'$gt': xyzd[0]}},
        {'$and': [{'mayor': {'$eq': xyzd[0]}}, {'minor': {'$gt': xyzd[1]}}]},
        {'$and': [{'mayor': {'$eq': xyzd[0]}}, {'minor': {'$eq': xyzd[1]}}, {'patch': {'$gt': xyzd[2]}}]},
        {'$and': [{'mayor': {'$eq': xyzd[0]}}, {'minor': {'$eq': xyzd[1]}}, {'patch': {'$eq': xyzd[2]}}, {'build_number': {'$gt': xyzd[3]}}]}
    ]}

async def less_than_query(xyzd: list[int]) -> dict:
    return {'$or': [
        {'mayor': {'$lt': xyzd[0]}}, 
        {'$and': [{'mayor': {'$eq': xyzd[0]}}, {'minor': {'$lt': xyzd[1]}}]}, 
        {'$and': [{'mayor': {'$eq': xyzd[0]}}, {'minor': {'$eq': xyzd[1]}}, {'patch': {'$lt': xyzd[2]}}]},
        {'$and': [{'mayor': {'$eq': xyzd[0]}}, {'minor': {'$eq': xyzd[1]}}, {'patch': {'$eq': xyzd[2]}}, {'build_number': {'$lt': xyzd[3]}}]}
    ]}

async def not_equal_query(xyzd: list[int]) -> dict:
    return {'$or': [
        {'mayor': {'$ne': xyzd[0]}},
        {'minor': {'$ne': xyzd[1]}},
        {'patch': {'$ne': xyzd[2]}},
        {'build_number': {'$ne': xyzd[3]}}
    ]}

async def greater_or_equal_than_query(xyzd: list[int]) -> dict:
    return {'$or': [await equal_query(xyzd), await greater_than_query(xyzd)]}

async def less_or_equal_than_query(xyzd: list[int]) -> dict:
    return {'$or': [await equal_query(xyzd), await less_than_query(xyzd)]}

async def approx_gt_patch(xyzd: list[int]) -> dict:
    up_xyzd = await get_up(xyzd)
    return {'$and': [await greater_or_equal_than_query(xyzd), await less_than_query(up_xyzd)]}

async def approx_gt_minor(xyzd: list[int], number_of_elements: int) -> dict:
    up_xyzd = copy(xyzd)
    if number_of_elements != 1:
        up_xyzd[1] = up_xyzd[1] + 1
        return {'$and': [await greater_or_equal_than_query(xyzd), await less_than_query(up_xyzd)]}
    up_xyzd[0] = up_xyzd[0] + 1
    return {'$and': [await greater_or_equal_than_query(xyzd), await less_than_query(up_xyzd)]}

async def get_up(xyzd: list[int]) -> list[int]:
    for i in range(0, 4):
        if xyzd[i] != 0:
            up_xyzd = copy(xyzd)
            up_xyzd[i] = up_xyzd[i] + 1
            return up_xyzd
    return xyzd