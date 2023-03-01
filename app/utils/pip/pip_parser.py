from app.utils import sanitize_version


async def parse_pip_constraints(raw_constraints: str) -> dict[str, str] | str:
    if raw_constraints:
        raw_constraints = raw_constraints.replace(' ', '')
        ctcs = {}

        for ctc in raw_constraints.split(','):
            positions: list[int] = [ctc.index(char) for char in ctc if char.isdigit()]
            if not positions:
                continue

            pos: int = positions[0]
            ctcs[ctc[:pos]] = ctc[pos:]

        if ctcs:
            return await clean_pip_constraints(ctcs)

    return 'any'


async def clean_pip_constraints(raw_constraints: dict[str, str]) -> dict[str, str]:
    constraints = {}
    for operator, version in raw_constraints.items():

        if operator == '==' and '*' in version:
            pos = version.find('*')
            version = version[:pos - 1]
            constraints['>='] = version
            constraints['<'] = version[:pos - 2] + str(int(version[pos - 2]) + 1)
            continue

        if operator == '!=' and '*' in version:
            pos = version.find('*')
            version = version[:pos - 1]
            constraints['<'] = version
            constraints['>='] = version[:pos - 2] + str(int(version[pos - 2]) + 1)
            continue

        if operator in ('~=', '~>'):
            parts = version.split('.')
            parts[-2] = str(int(parts[-2]) + 1)
            parts.pop()
            constraints['>='] = version
            constraints['<'] = '.'.join(parts)
            continue

        if not version.replace('.', '').isdigit():
            version = await sanitize_version(version)

        constraints[operator] = version

    return constraints