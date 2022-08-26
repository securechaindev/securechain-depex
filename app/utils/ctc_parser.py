def parse_constraints(raw_constraints: list[list[str]]) -> list[list[str]]:
    for raw_constraint in raw_constraints:
        
        if '||' in raw_constraint[0] or '||' in raw_constraint[1]:
            raw_constraint[0] = '!='
            raw_constraint[1] = raw_constraint[1].split(' ')[0]
        elif '*' in raw_constraint[1]:
            raw_constraint[0] = '~>'
            raw_constraint[1] = raw_constraint[1].replace('*', '0')

    return raw_constraints