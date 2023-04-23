PIP = 'PIP'


async def get_manager(filename: str) -> str | None:
    if '.txt' in filename:
        return PIP
    match filename:
        case 'setup.py':
            return PIP
        case _:
            return None