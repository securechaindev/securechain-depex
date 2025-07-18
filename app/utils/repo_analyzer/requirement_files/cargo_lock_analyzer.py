from toml import load


async def analyze_cargo_lock(
    requirement_files: dict[str, dict[str, dict | str]],
    repository_path: str,
    requirement_file_name: str,
) -> dict[str, dict[str, dict | str]]:
    requirement_file_name = requirement_file_name.replace("/master/", "").replace(
        "/main/", ""
    )
    requirement_files[requirement_file_name] = {
        "manager": "Cargo",
        "dependencies": {},
    }
    try:
        with open(f"{repository_path}/{requirement_file_name}", "r") as file:
            data = load(file)
            dependencies = {}
            if "package" in data:
                for package in data["package"]:
                    version = package["version"]
                    dependencies[package["name"]] = f"== {version}"
            if dependencies:
                requirement_files[requirement_file_name]["dependencies"] = dependencies
    except Exception as e:
        pass
    return requirement_files
