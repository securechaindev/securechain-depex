from __future__ import annotations

from asyncio import run
from json import load
from typing import ClassVar
from xml.etree.ElementTree import parse

from .base_analyzer import RequirementFileAnalyzer
from .cargo_lock_analyzer import CargoLockAnalyzer
from .cargo_toml_analyzer import CargoTomlAnalyzer
from .cyclonedx_sbom_analyzer import CycloneDxSbomAnalyzer
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
            "cyclonedx": CycloneDxSbomAnalyzer(),
            # "spdx": SpdxSbomAnalyzer(),  # Future: SPDX format support
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

    def get_analyzer(self, filename: str, repository_path: str) -> RequirementFileAnalyzer | None:
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

        if self.is_sbom_file(file_basename) and repository_path:
            sbom_format = self.detect_sbom_format(filename, repository_path)
            if sbom_format:
                return self.analyzers.get(sbom_format)

        return None

    def is_sbom_file(self, filename: str) -> bool:
        file_lower = filename.lower()
        return (
            "sbom" in file_lower or
            "bom" in file_lower or
            filename.endswith(".cdx.json") or
            filename.endswith(".cdx.xml") or
            filename.endswith(".spdx.xml") or
            filename.endswith(".spdx.xml")
        )

    def detect_sbom_format(self, filename: str, repository_path: str) -> str | None:
        filepath = f"{repository_path}/{filename}"

        try:
            if filename.endswith(".json"):
                return self.detect_json_sbom_format(filepath)
            elif filename.endswith(".xml"):
                return self.detect_xml_sbom_format(filepath)
        except Exception:
            pass

        return None

    def detect_json_sbom_format(self, filepath: str) -> str | None:
        try:
            with open(filepath, encoding="utf-8") as file:
                data = load(file)

                if data.get("bomFormat") == "CycloneDX":
                    return "cyclonedx"

                if data.get("spdxVersion"):
                    return "spdx"

        except Exception:
            pass

        return None

    def detect_xml_sbom_format(self, filepath: str) -> str | None:
        try:
            tree = parse(filepath)
            root = tree.getroot()

            namespace = ""
            if root.tag.startswith("{"):
                namespace = root.tag.split("}")[0] + "}"

            if "cyclonedx.org" in namespace.lower() and root.tag.endswith("bom"):
                return "cyclonedx"

            if "spdx.org" in namespace.lower():
                return "spdx"

        except Exception:
            pass

        return None

    def analyze(
        self,
        requirement_files: dict[str, dict[str, dict | str]],
        repository_path: str,
        filename: str,
    ) -> dict[str, dict[str, dict | str]]:
        analyzer: RequirementFileAnalyzer | None = self.get_analyzer(filename, repository_path)
        if analyzer:
            return run(
                analyzer.analyze(requirement_files, repository_path, filename)
            )
        return requirement_files
