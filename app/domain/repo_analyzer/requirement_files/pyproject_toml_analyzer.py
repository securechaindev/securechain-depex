from toml import load

from .base_analyzer import RequirementFileAnalyzer
from .pypi_utils import PyPiConstraintParser


class PyprojectTomlAnalyzer(RequirementFileAnalyzer):
    def __init__(self):
        super().__init__("PyPI")

    def _parse_file(self, repository_path: str, filename: str) -> dict[str, str]:
        packages = {}
        file = load(f"{repository_path}/{filename}")
        if "project" in file and "dependencies" in file["project"]:
            for dependency in file["project"]["dependencies"]:
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
                    pos_1 = PyPiConstraintParser.get_first_op_position(dependency[0], ["["])
                    pos_2 = PyPiConstraintParser.get_first_op_position(dependency[0], ["]"]) + 1
                    dependency[0] = dependency[0][:pos_1] + dependency[0][pos_2:]
                dependency = (
                    dependency[0]
                    .replace("(", "")
                    .replace(")", "")
                    .replace(" ", "")
                    .replace("'", "")
                )
                pos = PyPiConstraintParser.get_first_op_position(dependency, ["<", ">", "=", "!", "~"])
                packages[dependency[:pos].lower()] = PyPiConstraintParser.parse_pypi_constraints(
                    dependency[pos:]
                )
        return packages
