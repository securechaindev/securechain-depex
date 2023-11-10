async def get_first_position(data: str, operators: list[str]) -> int:
    if not any(operator in data for operator in operators):
        return len(data)
    for index, char in enumerate(data):
        if char in operators:
            return index
    return 0
