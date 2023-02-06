from app.utils.pip.pip_parser import parse_pip_constraints


async def parse_constraints(raw_constraints: str, manager: str) -> dict[str, str] | str:
    match manager:
        case 'PIP':
            return await parse_pip_constraints(raw_constraints)
        case _:
            return await parse_pip_constraints(raw_constraints)