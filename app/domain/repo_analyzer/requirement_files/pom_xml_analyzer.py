from xml.etree.ElementTree import fromstring

from .base_analyzer import RequirementFileAnalyzer


class PomXmlAnalyzer(RequirementFileAnalyzer):
    def __init__(self):
        super().__init__("Maven")

    def parse_file(self, repository_path: str, filename: str) -> dict[str, str]:
        packages = {}
        with open(f"{repository_path}/{filename}", encoding="utf-8") as file:
            pom_xml = file.read()
        root = fromstring(pom_xml)
        namespace = "{http://maven.apache.org/POM/4.0.0}"
        dependencies = root.findall(f".//{namespace}dependency")
        properties = {
            prop.tag.replace(namespace, ""): prop.text
            for prop in root.findall(f".//{namespace}properties/*")
        }
        for dep in dependencies:
            group_id = dep.find(f"{namespace}groupId")
            artifact_id = dep.find(f"{namespace}artifactId")
            version = dep.find(f"{namespace}version")
            if group_id is None or artifact_id is None:
                continue
            group_id_text = group_id.text or ""
            artifact_id_text = artifact_id.text or ""
            version_text = version.text if version is not None and version.text is not None else "any"
            if version_text.startswith("${") and version_text.endswith("}"):
                property_key = version_text[2:-1]
                version_text = properties.get(property_key, "any")
            if version_text != "any" and version_text is not None and not any(
                char in version_text for char in ["[", "]", "(", ")"]
            ):
                version_text = f"[{version_text}]"
            packages[f"{group_id_text}:{artifact_id_text}"] = version_text
        return packages
