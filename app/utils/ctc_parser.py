def parse_constraints(parts: list[str]) -> list[str]:
    constraints = []

    for part in parts:
        if '||' in part:
            attr = part.split(' ')
            constraint = '!= ' + attr[1]
        elif '*' in part:
            part = part.replace('*', '0').replace('=', '').strip()
            constraint = '~> ' + part
        else:
            constraint = part
        constraints.append(constraint)

    return constraints