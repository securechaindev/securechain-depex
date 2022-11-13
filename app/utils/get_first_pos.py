async def get_first_position(data: str, operators: list[str]) -> int:
    if not await have_any_op(data, operators):
        return len(data)

    return await search_position(data, operators)

async def have_any_op(data: str, operators: list[str]) -> bool:
    have_any_op = False

    for op in operators:
        if op in data:
            have_any_op = True
            break
    
    return have_any_op

async def search_position(data: str, operators: list[str]) -> int:
    for char in data:
        if char in operators:
            return data.index(char)

    return 0