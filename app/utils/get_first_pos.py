async def get_first_position(data: str) -> int:
    for char in data:
        if char in ('<', '>', '=', '!', '|', '^', '~'):
            return data.index(char)

    return len(data)