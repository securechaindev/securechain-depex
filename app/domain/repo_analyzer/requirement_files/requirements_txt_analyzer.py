from .base_analyzer import RequirementFileAnalyzer
from .pypi_utils import PyPiConstraintParser


class RequirementsTxtAnalyzer(RequirementFileAnalyzer):
    def __init__(self):
        super().__init__("PyPI")

    def _parse_file(self, repository_path: str, filename: str) -> dict[str, str]:
        packages = {}
        with open(f"{repository_path}/{filename}") as file:
            dependencies = []
            for line in file.readlines():
                if "#" not in line:
                    dependencies.append(line.strip().replace("\n", ""))

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
