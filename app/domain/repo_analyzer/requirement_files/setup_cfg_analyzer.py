from setuptools.config.setupcfg import read_configuration

from .base_analyzer import RequirementFileAnalyzer
from .pypi_utils import PyPiConstraintParser


class SetupCfgAnalyzer(RequirementFileAnalyzer):
    def __init__(self):
        super().__init__("PyPI")

    def parse_file(self, repository_path: str, filename: str) -> dict[str, str]:
        packages = {}
        file = read_configuration(f"{repository_path}/{filename}")
        if "install_requires" in file["options"]:
            for dependency in file["options"]["install_requires"]:
                dependency = dependency.split(";")

                if self.should_skip_dependency(dependency):
                    continue

                if "[" in dependency[0]:
                    pos_1 = PyPiConstraintParser.get_first_op_position(dependency[0], ["["])
                    pos_2 = PyPiConstraintParser.get_first_op_position(dependency[0], ["]"]) + 1
                    dependency[0] = dependency[0][:pos_1] + dependency[0][pos_2:]

                dependency = self.clean_dependency_name(dependency[0])
                pos = PyPiConstraintParser.get_first_op_position(dependency, ["<", ">", "=", "!", "~"])
                packages[dependency[:pos].lower()] = PyPiConstraintParser.parse_pypi_constraints(
                    dependency[pos:]
                )
        return packages
