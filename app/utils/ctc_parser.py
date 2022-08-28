def parse_constraints(raw_constraints: str):
    raw_constraints = raw_constraints.replace(' ', '')

    if raw_constraints:
        ctcs = []
        for ctc in raw_constraints.split(','):
            pos: int = [ctc.index(char) for char in ctc if char.isdigit()][0]
            ctcs.append([ctc[:pos], ctc[pos:]])
    else:
        ctcs = ['Any']

    return clean_constraints(ctcs)

def clean_constraints(raw_constraints: list[list[str]]) -> list[list[str]]:
    for raw_constraint in raw_constraints:
        
        if '||' in raw_constraint[0] or '||' in raw_constraint[1]:
            raw_constraint[0] = '!='
            raw_constraint[1] = raw_constraint[1].split(' ')[0]
        elif '*' in raw_constraint[1]:
            raw_constraint[0] = '~>'
            raw_constraint[1] = raw_constraint[1].replace('*', '0')

    return raw_constraints