from json import load

from .base_analyzer import RequirementFileAnalyzer


class PackageJsonAnalyzer(RequirementFileAnalyzer):
    def __init__(self):
        super().__init__("NPM")

    async def _parse_file(self, repository_path: str, filename: str) -> dict[str, str]:
        with open(f"{repository_path}/{filename}") as file:
            data = load(file)
            return data.get("dependencies", {})
