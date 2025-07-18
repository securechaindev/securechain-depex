import re


async def analyze_gemfile(
    requirement_files: dict[str, dict[str, dict | str]],
    repository_path: str,
    requirement_file_name: str,
) -> dict[str, dict[str, dict | str]]:
    requirement_file_name = requirement_file_name.replace("/master/", "").replace(
        "/main/", ""
    )
    requirement_files[requirement_file_name] = {
        "manager": "RubyGems",
        "dependencies": {},
    }
    try:
        with open(f"{repository_path}/{requirement_file_name}", "r") as file:
            gemfile_content = file.read()
            dependencies = {}
            gem_pattern = re.compile(r"gem\s+'([^']+)'\s*,?\s*'([^']+)'")
            matches = gem_pattern.findall(gemfile_content)
            for gem, version in matches:
                if version.count(".") == 2 and not any(op in version for op in ['<', '>', '=']):
                    dependencies[gem] = f"== {version}"
                else:
                    dependencies[gem] = version
            if dependencies:
                requirement_files[requirement_file_name]["dependencies"] = dependencies
    except Exception as e:
        pass
    return requirement_files
