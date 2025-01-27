from re import findall

from app.utils import get_first_position, parse_pypi_constraints


async def analyze_setup_py(
    requirement_files: dict[str, dict[str, dict | str]],
    repository_path: str,
    requirement_file_name: str,
) -> dict[str, dict[str, dict | str]]:
    try:
        with open(repository_path + requirement_file_name) as f:
            matches: list[str] = findall(
                r"(?:install_requires|requires)\s*=\s*\[([^\]]+)\]", f.read()
            )
            dependencies = []
            if matches:
                matches = matches[0].split("\n")[1:-1]
                for dep in matches:
                    if "#" not in dep:
                        dependencies.append(
                            dep.strip().replace('"', "").replace("'", "")
                        )
    except Exception as _:
        return requirement_files
    requirement_file_name = requirement_file_name.replace("/master/", "").replace(
        "/main/", ""
    )
    requirement_files[requirement_file_name] = {
        "manager": "pypi",
        "dependencies": {},
    }
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
            {dependency[:pos].lower(): await parse_pypi_constraints(dependency[pos:])}
        )
    return requirement_files
