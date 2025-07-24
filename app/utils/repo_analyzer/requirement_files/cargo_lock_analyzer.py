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
        "requirement": {},
    }
    try:
        with open(f"{repository_path}/{requirement_file_name}") as file:
            data = load(file)
            requirement = {}
            if "package" in data:
                for package in data["package"]:
                    version = package["version"]
                    requirement[package["name"]] = f"== {version}"
            requirement_files[requirement_file_name]["requirement"] = requirement
    except Exception:
        pass
    return requirement_files
