PIP = 'PIP'
NPM = 'NPM'
MVN = 'MVN'


async def get_manager(file_name: str) -> str:
    if '.txt' in file_name:
        return PIP
    match file_name:
        case 'setup.py':
            return PIP
        case 'pipfile.lock':
            return PIP
        case 'pipfile':
            return PIP
        case 'package-lock.json':
            return NPM
        case 'package.json':
            return NPM
        case 'pom.xml':
            return MVN
        case _:
            return ''