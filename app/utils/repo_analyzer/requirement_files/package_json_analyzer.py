from json import load


async def analyze_package_json(
    requirement_files: dict[str, dict[str, dict | str]],
    repository_path: str,
    requirement_file_name: str,
) -> dict[str, dict[str, dict | str]]:
    file = open(f"{repository_path}/{requirement_file_name}")
    requirement_file_name = requirement_file_name.replace("/master/", "").replace(
        "/main/", ""
    )
    requirement_files[requirement_file_name] = {
        "manager": "NPM",
        "requirement": {},
    }
    try:
        data = load(file)
        requirement_files[requirement_file_name]["requirement"] = (
            data["dependencies"] if "dependencies" in data else {}
        )
    except Exception:
        pass
    return requirement_files
