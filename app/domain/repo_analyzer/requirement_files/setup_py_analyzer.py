from re import findall

from .base_analyzer import RequirementFileAnalyzer
from .pypi_utils import PyPiConstraintParser


class SetupPyAnalyzer(RequirementFileAnalyzer):
    def __init__(self):
        super().__init__("PyPI")

    def parse_file(self, repository_path: str, filename: str) -> dict[str, str]:
        packages = {}
        with open(f"{repository_path}/{filename}") as f:
            matches: list[str] = findall(
                r"(?:install_requires|requires)\s*=\s*\[([^\]]+)\]", f.read()
            )
            dependencies = []
            if matches:
                matches = matches[0].split("\n")[1:-1]
                for dep in matches:
                    if "#" not in dep:
                        dependencies.append(
                            dep.strip().replace('"', "").replace("'", "").rstrip(",")
                        )

        for dependency in dependencies:
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
