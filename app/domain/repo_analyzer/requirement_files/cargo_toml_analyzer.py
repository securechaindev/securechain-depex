from toml import load

from .base_analyzer import RequirementFileAnalyzer


class CargoTomlAnalyzer(RequirementFileAnalyzer):
    def __init__(self):
        super().__init__("Cargo")

    def parse_file(self, repository_path: str, filename: str) -> dict[str, str]:
        packages = {}
        with open(f"{repository_path}/{filename}") as file:
            data = load(file)
            if "dependencies" in data:
                for package, version in data["dependencies"].items():
                    packages[package] = self.normalize_version(version)
        return packages
