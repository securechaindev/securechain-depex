from __future__ import annotations

from asyncio import run
from typing import ClassVar

from .base_analyzer import RequirementFileAnalyzer
from .cargo_lock_analyzer import CargoLockAnalyzer
from .cargo_toml_analyzer import CargoTomlAnalyzer
from .gemfile_analyzer import GemfileAnalyzer
from .gemfile_lock_analyzer import GemfileLockAnalyzer
from .package_config_analyzer import PackageConfigAnalyzer
from .package_json_analyzer import PackageJsonAnalyzer
from .package_lock_json_analyzer import PackageLockJsonAnalyzer
from .pom_xml_analyzer import PomXmlAnalyzer
from .pyproject_toml_analyzer import PyprojectTomlAnalyzer
from .requirements_txt_analyzer import RequirementsTxtAnalyzer
from .setup_cfg_analyzer import SetupCfgAnalyzer
from .setup_py_analyzer import SetupPyAnalyzer


class AnalyzerRegistry:
    instance: ClassVar[AnalyzerRegistry | None] = None
    analyzers: dict[str, RequirementFileAnalyzer]

    def __new__(cls) -> AnalyzerRegistry:
        if cls.instance is None:
            cls.instance = super().__new__(cls)
            cls.instance.initialize()
        return cls.instance

    def initialize(self) -> None:
        self.analyzers = {
            "Cargo.lock": CargoLockAnalyzer(),
            "Cargo.toml": CargoTomlAnalyzer(),
            "Gemfile": GemfileAnalyzer(),
            "Gemfile.lock": GemfileLockAnalyzer(),
            "packages.config": PackageConfigAnalyzer(),
            "package.json": PackageJsonAnalyzer(),
            "package-lock.json": PackageLockJsonAnalyzer(),
            "pom.xml": PomXmlAnalyzer(),
            "pyproject.toml": PyprojectTomlAnalyzer(),
            "requirements.txt": RequirementsTxtAnalyzer(),
            "setup.cfg": SetupCfgAnalyzer(),
            "setup.py": SetupPyAnalyzer(),
        }

    def get_analyzer(self, filename: str) -> RequirementFileAnalyzer | None:
        file_basename = filename.split("/")[-1]

        if file_basename in self.analyzers:
            return self.analyzers[file_basename]

        file_lower = file_basename.lower()

        if "requirements" in file_lower and file_basename.endswith(".txt"):
            return self.analyzers["requirements.txt"]

        if "gemfile" in file_lower and not file_basename.endswith((".lock", ".txt")):
            return self.analyzers.get("Gemfile")

        if "package" in file_lower and file_basename.endswith(".json") and "lock" not in file_lower:
            return self.analyzers.get("package.json")

        if "package-lock" in file_lower and file_basename.endswith(".json"):
            return self.analyzers.get("package-lock.json")

        return None

    def analyze(
        self,
        requirement_files: dict[str, dict[str, dict | str]],
        repository_path: str,
        filename: str,
    ) -> dict[str, dict[str, dict | str]]:
        analyzer: RequirementFileAnalyzer | None = self.get_analyzer(filename)
        if analyzer:
            return run(
                analyzer.analyze(requirement_files, repository_path, filename)
            )
        return requirement_files
