def parse_constraints(parts: list[str]) -> list[str]:
    constraints = list()

    for part in parts:
        if part.__contains__('||'):
            attr = part.split(' ')
            constraint = '!= ' + attr[1]
        elif part.__contains__('*'):
            part = part.replace('*', '0').replace('=', '').strip()
            constraint = '~> ' + part
        else:
            constraint = part
        constraints.append(constraint)

    return constraints