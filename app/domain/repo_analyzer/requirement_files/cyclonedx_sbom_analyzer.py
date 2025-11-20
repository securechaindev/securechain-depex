from json import load
from xml.etree.ElementTree import parse

from packageurl import PackageURL

from app.constants import PurlTypeToManager

from .base_analyzer import RequirementFileAnalyzer


class CycloneDxSbomAnalyzer(RequirementFileAnalyzer):
    def __init__(self):
        super().__init__("ANY")

    async def analyze(
        self,
        requirement_files: dict[str, dict[str, dict | str]],
        repository_path: str,
        requirement_file_name: str,
    ) -> dict[str, dict[str, dict | str]]:
        requirement_file_name = self.normalize_filename(requirement_file_name)

        try:
            packages_with_manager = self.parse_file(repository_path, requirement_file_name)

            if packages_with_manager:
                requirement_files[requirement_file_name] = {
                    "manager": "ANY",
                    "packages": packages_with_manager,
                }
        except Exception:
            pass

        return requirement_files

    def parse_file(self, repository_path: str, filename: str) -> dict[str, str]:
        filepath = f"{repository_path}/{filename}"

        try:
            if filename.endswith(".json"):
                data = self.parse_json(filepath)
            elif filename.endswith(".xml"):
                data = self.parse_xml(filepath)
            else:
                return {}

            return self.extract_dependencies(data)
        except Exception:
            return {}

    def parse_json(self, filepath: str) -> dict:
        with open(filepath, encoding="utf-8") as file:
            return load(file)

    def parse_xml(self, filepath: str) -> dict:
        tree = parse(filepath)
        root = tree.getroot()

        namespace = ""
        if root.tag.startswith("{"):
            namespace = root.tag.split("}")[0] + "}"

        components = []
        components_elem = root.find(f"{namespace}components")
        if components_elem is not None:
            for component in components_elem.findall(f"{namespace}component"):
                purl_elem = component.find(f"{namespace}purl")
                if purl_elem is not None and purl_elem.text:
                    components.append({"purl": purl_elem.text})

        return {"components": components}

    def extract_dependencies(self, data: dict) -> dict[str, str]:
        packages: dict[str, str] = {}

        components = data.get("components", [])
        if not components:
            return packages

        for component in components:
            purl_str = component.get("purl")
            if not purl_str:
                continue

            try:
                purl = PackageURL.from_string(purl_str)
            except Exception:
                continue

            package_type = purl.type

            manager = PurlTypeToManager.MAPPING.get(package_type)
            if not manager:
                continue

            if package_type == "maven":
                package_id = f"{purl.namespace}:{purl.name}" if purl.namespace else purl.name
            elif package_type in ["npm", "cargo"]:
                package_id = f"{purl.namespace}/{purl.name}" if purl.namespace else purl.name
            else:
                package_id = purl.name

            if not package_id:
                continue

            version = self.normalize_version_for_type(purl.version, package_type) if purl.version else "any"

            prefixed_key = f"{manager}:{package_id}"
            packages[prefixed_key] = version

        return packages

    def normalize_version_for_type(self, version: str, package_type: str) -> str:
        if package_type == "maven":
            return f"[{version}]"
        elif package_type == "gem":
            return f"={version}"
        else:
            return f"=={version}"
