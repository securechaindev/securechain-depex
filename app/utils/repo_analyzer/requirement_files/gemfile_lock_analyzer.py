import re


async def analyze_gemfile_lock(
    requirement_files: dict[str, dict[str, dict | str]],
    repository_path: str,
    requirement_file_name: str,
) -> dict[str, dict[str, dict | str]]:
    requirement_file_name = requirement_file_name.replace("/master/", "").replace(
        "/main/", ""
    )
    requirement_files[requirement_file_name] = {
        "manager": "RubyGems",
        "requirement": {},
    }
    try:
        with open(f"{repository_path}/{requirement_file_name}") as file:
            gemfile_content = file.read()
            requirement = {}
            gem_pattern = re.compile(r"\s+(\S+)\s+\(([^)]+)\)")
            matches = gem_pattern.findall(gemfile_content)
            for gem, version in matches:
                if version.count(".") == 2 and not any(op in version for op in ['<', '>', '=']):
                    requirement[gem] = f"== {version}"
                else:
                    requirement[gem] = version
            requirement_files[requirement_file_name]["requirement"] = requirement
    except Exception:
        pass
    return requirement_files
