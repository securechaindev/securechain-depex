from xml.etree import ElementTree

from .base_analyzer import RequirementFileAnalyzer


class PackageConfigAnalyzer(RequirementFileAnalyzer):
    def __init__(self):
        super().__init__("NuGet")

    def parse_file(self, repository_path: str, filename: str) -> dict[str, str]:
        packages = {}
        tree = ElementTree.parse(f"{repository_path}/{filename}")
        root = tree.getroot()
        for package in root.findall("package"):
            name = package.get("id")
            version = package.get("version")
            if name and version:
                if (
                    version.count(".") == 2
                    and not any(op in version for op in ["<", ">", "="])
                ):
                    packages[name] = f"== {version}"
                else:
                    packages[name] = version
        return packages
