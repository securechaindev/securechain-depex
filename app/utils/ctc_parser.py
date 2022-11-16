async def parse_constraints(raw_constraints: str) -> dict[str, str] | str:
    if raw_constraints:
        raw_constraints = raw_constraints.replace(' ', '')
        ctcs = {}

        for ctc in raw_constraints.split(','):
            pos: int = [ctc.index(char) for char in ctc if char.isdigit()][0]
            ctcs[ctc[:pos]] = ctc[pos:]

        return await clean_constraints(ctcs)

    return 'any'


async def clean_constraints(raw_constraints: dict[str, str]) -> dict[str, str]:
    constrains = {}
    for operator, version in raw_constraints.items():
        if not version.replace('.', '').isdigit():
            version = await sanitize_version(version)
        if '||' in operator or '||' in version:
            operator = '!='
            version = version.split('|')[0]
        elif '*' in version:
            operator = '~>'
            version = version.replace('*', '0')

        constrains[operator] = version

    return constrains


async def sanitize_version(version: str) -> str:
    parts = []
    for part in version.split('.'):
        if part.isdigit():
            parts.append(part)
        elif part[0].isdigit():
            parts.append(part[0])
        else:
            parts.append('0')
    return '.'.join(parts)