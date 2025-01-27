from toml import load

from app.utils import get_first_position, parse_pypi_constraints


async def analyze_pyproject_toml(
    requirement_files: dict[str, dict[str, dict | str]],
    repository_path: str,
    requirement_file_name: str,
) -> dict[str, dict[str, dict | str]]:
    try:
        file = load(repository_path + requirement_file_name)
    except Exception as _:
        return requirement_files
    requirement_file_name = requirement_file_name.replace("/master/", "").replace(
        "/main/", ""
    )
    requirement_files[requirement_file_name] = {
        "manager": "pypi",
        "dependencies": {},
    }
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
                pos_1 = await get_first_position(dependency[0], ["["])
                pos_2 = await get_first_position(dependency[0], ["]"]) + 1
                dependency[0] = dependency[0][:pos_1] + dependency[0][pos_2:]
            dependency = (
                dependency[0]
                .replace("(", "")
                .replace(")", "")
                .replace(" ", "")
                .replace("'", "")
            )
            pos = await get_first_position(dependency, ["<", ">", "=", "!", "~"])
            requirement_files[requirement_file_name]["dependencies"].update(
                {
                    dependency[:pos].lower(): await parse_pypi_constraints(
                        dependency[pos:]
                    )
                }
            )
    return requirement_files
