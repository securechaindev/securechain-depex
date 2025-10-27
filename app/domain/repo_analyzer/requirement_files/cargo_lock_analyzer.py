from toml import load

from .base_analyzer import RequirementFileAnalyzer


class CargoLockAnalyzer(RequirementFileAnalyzer):
    def __init__(self):
        super().__init__("Cargo")

    def _parse_file(self, repository_path: str, filename: str) -> dict[str, str]:
        packages = {}
        with open(f"{repository_path}/{filename}") as file:
            data = load(file)
            if "package" in data:
                for package in data["package"]:
                    version = package["version"]
                    packages[package["name"]] = f"== {version}"
        return packages
