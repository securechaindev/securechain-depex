from abc import ABC, abstractmethod

from regex import findall

from app.settings import settings


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
        version_pattern = r'([<>=!]+)\s*["\']?(\d+)(?:\.(\d+))?(?:\.(\d+))?["\']?'
        matches = findall(version_pattern, version_marker)

        if not matches:
            return True

        min_major = settings.MIN_PYTHON_VERSION_MAJOR
        min_minor = settings.MIN_PYTHON_VERSION_MINOR

        for operator, major, minor, _ in matches:
            major_ver = int(major)
            minor_ver = int(minor) if minor else 0

            if major_ver < 3:
                if operator.startswith('>'):
                    continue
                return False

            if major_ver == 3:
                if operator == '==':
                    return (major_ver, minor_ver) >= (min_major, min_minor)
                elif operator.startswith('>='):
                    return True
                elif operator.startswith('>'):
                    return (min_major, min_minor) > (major_ver, minor_ver)
                elif operator.startswith('<='):
                    return True
                elif operator.startswith('<'):
                    return (major_ver, minor_ver) > (min_major, min_minor)

        return True

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
