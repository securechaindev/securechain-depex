from setuptools.config.setupcfg import read_configuration

from .base_analyzer import RequirementFileAnalyzer
from .pypi_utils import PyPiConstraintParser


class SetupCfgAnalyzer(RequirementFileAnalyzer):
    def __init__(self):
        super().__init__("PyPI")

    async def _parse_file(self, repository_path: str, filename: str) -> dict[str, str]:
        packages = {}
        file = read_configuration(f"{repository_path}/{filename}")
        if "install_requires" in file["options"]:
            for dependency in file["options"]["install_requires"]:
                dependency = dependency.split(";")
                if len(dependency) > 1:
                    if "extra" in dependency[1]:
                        continue
                    python_version = (
                        '== "3.9"' in dependency[1]
                        or '<= "3.9"' in dependency[1]
                        or '>= "3.9"' in dependency[1]
                        or '>= "3"' in dependency[1]
                        or '<= "3"' in dependency[1]
                        or '>= "2' in dependency[1]
                        or '> "2' in dependency[1]
                    )
                    if "python_version" in dependency[1] and not python_version:
                        continue
                if "[" in dependency[0]:
                    pos_1 = await PyPiConstraintParser.get_first_op_position(dependency[0], ["["])
                    pos_2 = await PyPiConstraintParser.get_first_op_position(dependency[0], ["]"]) + 1
                    dependency[0] = dependency[0][:pos_1] + dependency[0][pos_2:]
                dependency = (
                    dependency[0]
                    .replace("(", "")
                    .replace(")", "")
                    .replace(" ", "")
                    .replace("'", "")
                )
                pos = await PyPiConstraintParser.get_first_op_position(dependency, ["<", ">", "=", "!", "~"])
                packages[dependency[:pos].lower()] = await PyPiConstraintParser.parse_pypi_constraints(
                    dependency[pos:]
                )
        return packages
