PIP = 'PIP'
NPM = 'NPM'
MVN = 'MVN'


async def get_manager(file_name: str) -> str:
    pip_files = ('.txt', 'setup.py', 'pipfile.lock', 'pipfile', 'pyproject.toml')
    npm_files = ('package-lock.json', 'package.json')
    mvn_files = ['pom.xml']
    if any(extension in file_name for extension in pip_files):
        return PIP
    if any(extension in file_name for extension in npm_files):
        return NPM
    if any(extension in file_name for extension in mvn_files):
        return MVN
    return ''