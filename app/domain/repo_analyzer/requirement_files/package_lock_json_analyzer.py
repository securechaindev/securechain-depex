from json import load

from .base_analyzer import RequirementFileAnalyzer


class PackageLockJsonAnalyzer(RequirementFileAnalyzer):
    def __init__(self):
        super().__init__("NPM")

    def parse_file(self, repository_path: str, filename: str) -> dict[str, str]:
        packages = {}
        with open(f"{repository_path}/{filename}") as file:
            data = load(file)
            if "dependencies" in data:
                for package, details in data["dependencies"].items():
                    version = details.get("version")
                    if (
                        version
                        and version.count(".") == 2
                        and not any(op in version for op in ["<", ">", "="])
                    ):
                        packages[package] = f"== {version}"
                    else:
                        packages[package] = version
        return packages
