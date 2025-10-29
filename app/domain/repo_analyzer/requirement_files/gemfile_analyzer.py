from regex import compile

from .base_analyzer import RequirementFileAnalyzer


class GemfileAnalyzer(RequirementFileAnalyzer):
    def __init__(self):
        super().__init__("RubyGems")

    def parse_file(self, repository_path: str, filename: str) -> dict[str, str]:
        packages = {}
        with open(f"{repository_path}/{filename}") as file:
            gemfile_content = file.read()
            gem_pattern = compile(r"gem\s+'([^']+)'\s*,?\s*'([^']+)'")
            matches = gem_pattern.findall(gemfile_content)
            for gem, version in matches:
                if (
                    version.count(".") == 2
                    and not any(op in version for op in ["<", ">", "="])
                ):
                    packages[gem] = f"== {version}"
                else:
                    packages[gem] = version
        return packages
