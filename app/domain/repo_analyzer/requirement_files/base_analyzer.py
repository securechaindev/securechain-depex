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
            packages = await self._parse_file(repository_path, requirement_file_name)
            requirement_files[requirement_file_name]["packages"] = packages
        except Exception:
            pass

        return requirement_files

    @abstractmethod
    async def _parse_file(self, repository_path: str, filename: str) -> dict[str, str]:
        pass

    def _normalize_filename(self, filename: str) -> str:
        return filename.replace("/master/", "").replace("/main/", "")

    def _normalize_version(self, version: str) -> str:
        if version.count(".") == 2 and not any(op in version for op in ["<", ">", "=", "!", "~"]):
            return f"== {version}"
        return version
