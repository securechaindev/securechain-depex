from abc import ABC, abstractmethod


class RequirementFileAnalyzer(ABC):
    def __init__(self, manager: str):
        self.manager = manager

    async def analyze(
        self,
        requirement_files: dict[str, dict[str, dict | str]],
        repository_path: str,
        requirement_file_name: str,
    ) -> dict[str, dict[str, dict | str]]:
        requirement_file_name = self._normalize_filename(requirement_file_name)
        requirement_files[requirement_file_name] = {
            "manager": self.manager,
            "packages": {},
        }

        try:
            packages = self._parse_file(repository_path, requirement_file_name)
            requirement_files[requirement_file_name]["packages"] = packages
        except Exception:
            pass

        return requirement_files

    @abstractmethod
    def _parse_file(self, repository_path: str, filename: str) -> dict[str, str]:
        pass

    def _normalize_filename(self, filename: str) -> str:
        return filename.replace("/master/", "").replace("/main/", "")

    def _normalize_version(self, version: str) -> str:
        if version.count(".") == 2 and not any(op in version for op in ["<", ">", "=", "!", "~"]):
            return f"== {version}"
        return version

    @staticmethod
    def is_compatible_python_version(version_marker: str) -> bool:
        compatible_versions = (
            '== "3.9"' in version_marker
            or '<= "3.9"' in version_marker
            or '>= "3.9"' in version_marker
            or '>= "3"' in version_marker
            or '<= "3"' in version_marker
            or '>= "2' in version_marker
            or '> "2' in version_marker
        )
        return compatible_versions

    @staticmethod
    def should_skip_dependency(dependency_parts: list[str]) -> bool:
        if len(dependency_parts) <= 1:
            return False

        marker = dependency_parts[1]

        if "extra" in marker:
            return True

        if "python_version" in marker:
            return not RequirementFileAnalyzer.is_compatible_python_version(marker)

        return False

    @staticmethod
    def clean_dependency_name(dependency_name: str) -> str:
        cleaned = (
            dependency_name
            .replace("(", "")
            .replace(")", "")
            .replace(" ", "")
            .replace("'", "")
        )
        return cleaned
