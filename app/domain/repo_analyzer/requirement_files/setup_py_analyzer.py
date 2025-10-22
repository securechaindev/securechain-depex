from re import findall

from .base_analyzer import RequirementFileAnalyzer
from .pypi_utils import PyPiConstraintParser


class SetupPyAnalyzer(RequirementFileAnalyzer):
    def __init__(self):
        super().__init__("PyPI")

    async def _parse_file(self, repository_path: str, filename: str) -> dict[str, str]:
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
