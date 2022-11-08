from copy import copy


async def get_complete_query(constraints: dict[str, str], package_name: str) -> dict:
    query: dict = {'$and': [{'package': package_name}]}

    if constraints != 'any':
        for operator, version in constraints.items():
            query['$and'].append(await get_partial_query(operator, version))
    
    return query

async def get_partial_query(operator: str, version: str) -> dict:
    number_of_points = version.count('.')
    number_of_elements = number_of_points + 1
    xyzd = await sanitize(version, number_of_points)

    match operator:
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
            query = await approx_greater_than(xyzd)
        case '~>' | '~=' | '~':
            query = await approx_greater_than_minor(xyzd, number_of_elements)
        case _:
            query = {}

    return query

async def sanitize(version: str, number_of_points: int) -> list[int]:
    match number_of_points:
        case 0:
            version += '.0.0.0'
        case 1:
            version += '.0.0'
        case 2:
            version += '.0'
    return [int(part) for part in version.split('.')]

async def equal_query(xyzd: list[str]) -> dict:
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

async def approx_greater_than(xyzd: list[int]) -> dict:
    up_xyzd = await get_up(xyzd)
    return {'$and': [await greater_or_equal_than_query(xyzd), await less_than_query(up_xyzd)]}

async def get_up(xyzd: list[int]) -> list[int]:
    for i in range(0, 4):
        if xyzd[i] != 0:
            up_xyzd = copy(xyzd)
            up_xyzd[i] = up_xyzd[i] + 1
            return up_xyzd
    return xyzd

async def approx_greater_than_minor(xyzd: list[int], number_of_elements: int) -> dict:
    up_xyzd = copy(xyzd)
    if number_of_elements != 1:
        up_xyzd[1] = up_xyzd[1] + 1
        return {'$and': [await greater_or_equal_than_query(xyzd), await less_than_query(up_xyzd)]}
    up_xyzd[0] = up_xyzd[0] + 1
    return {'$and': [await greater_or_equal_than_query(xyzd), await less_than_query(up_xyzd)]}