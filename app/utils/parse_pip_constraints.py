# Need to parse pip constraits because Univers library dont support environment markers like .* version, ~= and === operators
# TODO: Wait to Univers solves this problem or make a pull request to Univers repository to solve this
async def parse_pip_constraints(raw_constraints: str) -> str:
    if raw_constraints:
        ctcs = []
        for ctc in raw_constraints.split(','):
            if '||' in ctc:
                release = ctc.split(' ')[-1]
                ctcs.append('!= ' + release)
            else:
                ctcs.append(ctc.strip())
        if ctcs:
            return await clean_pip_constraints(ctcs)
    return 'any'


async def clean_pip_constraints(raw_constraints: list[str]) -> str:
    constraints = []
    for raw_constraint in raw_constraints:
        if  ' ' not in raw_constraint:
            continue
        if ' ' not in raw_constraint:
            for index, char in enumerate(raw_constraint):
                if char.isdigit():
                    raw_constraint = raw_constraint[:index] + ' ' + raw_constraint[index:]
                    break
        operator, version = raw_constraint.strip().split(' ')
        if '==' in operator and '*' in version:
            pos = version.find('*')
            version = version[:pos - 1]
            constraints.append('>= ' + version)
            constraints.append('< ' + version[:pos - 2] + str(int(version[pos - 2]) + 1))
        elif '=' in operator and all([symbol not in operator for symbol in ['<', '>', '~', '!']]):
            constraints.append('== ' + version)
        elif '!=' in operator and '*' in version:
            pos = version.find('*')
            version = version[:pos - 1]
            constraints.append('< ' + version)
            constraints.append('>= ' + version[:pos - 2] + str(int(version[pos - 2]) + 1))
        elif any(symbol in operator for symbol in ('~=', '~>')):
            parts = version.split('.')
            parts[-2] = str(int(parts[-2]) + 1)
            parts.pop()
            constraints.append('>= ' + version)
            constraints.append('< ' + '.'.join(parts))
        else:
            constraints.append(operator + ' ' + version)
    return ', '.join(constraints)