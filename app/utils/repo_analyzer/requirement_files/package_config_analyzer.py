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
        "requirement": {},
    }
    try:
        tree = ElementTree.parse(f"{repository_path}/{requirement_file_name}")
        root = tree.getroot()
        requirement = {}
        for package in root.findall("package"):
            name = package.get("id")
            version = package.get("version")
            if name and version:
                if version.count(".") == 2 and not any(op in version for op in ['<', '>', '=']):
                    requirement[name] = f"== {version}"
                else:
                    requirement[name] = version
        requirement_files[requirement_file_name]["requirement"] = requirement
    except Exception:
        pass
    return requirement_files
