from xml.etree import ElementTree


async def analyze_packages_config(
    requirement_files: dict[str, dict[str, dict | str]],
    repository_path: str,
    requirement_file_name: str,
) -> dict[str, dict[str, dict | str]]:
    requirement_file_name = requirement_file_name.replace("/master/", "").replace(
        "/main/", ""
    )
    requirement_files[requirement_file_name] = {
        "manager": "NuGet",
        "dependencies": {},
    }
    try:
        tree = ElementTree.parse(f"{repository_path}/{requirement_file_name}")
        root = tree.getroot()
        dependencies = {}
        for package in root.findall("package"):
            name = package.get("id")
            version = package.get("version")
            if name and version:
                if version.count(".") == 2 and not any(op in version for op in ['<', '>', '=']):
                    dependencies[name] = f"== {version}"
                else:
                    dependencies[name] = version
        if dependencies:
            requirement_files[requirement_file_name]["dependencies"] = dependencies
    except Exception:
        pass
    return requirement_files
