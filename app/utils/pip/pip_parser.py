async def parse_pip_constraints(raw_constraints: str) -> list[str] | str:
    if raw_constraints:
        raw_constraints = raw_constraints.replace(' ', '')
        ctcs = []

        for ctc in raw_constraints.split(','):
            positions: list[int] = [ctc.index(char) for char in ctc if char.isdigit()]
            if not positions:
                continue

            pos: int = positions[0]
            ctcs.append(ctc[:pos] + ' ' + ctc[pos:])

        if ctcs:
            return await clean_pip_constraints(ctcs)

    return 'any'


async def clean_pip_constraints(ctcs: list[str]) -> list[str]:
    constraints = []
    for raw_constraint in ctcs:
        operator, version = raw_constraint.split(' ')

        if operator == '==' and '*' in version:
            pos = version.find('*')
            version = version[:pos - 1]
            constraints.append('>= ' + version)
            constraints.append('< ' + version[:pos - 2] + str(int(version[pos - 2]) + 1))
            continue

        if operator == '!=' and '*' in version:
            pos = version.find('*')
            version = version[:pos - 1]
            constraints.append('< ' + version)
            constraints.append('>= ' + version[:pos - 2] + str(int(version[pos - 2]) + 1))
            continue

        if operator in ('~=', '~>'):
            parts = version.split('.')
            parts[-2] = str(int(parts[-2]) + 1)
            parts.pop()
            constraints.append('>= ' + version)
            constraints.append('< ' + '.'.join(parts))
            continue

        constraints.append(operator + ' ' + version)

    return constraints