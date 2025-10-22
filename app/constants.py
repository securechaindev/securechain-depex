PYPI_FILES = ["pyproject.toml", "setup.cfg", "setup.py", "requirements.txt"]
NPM_FILES = ["package.json", "package-lock.json"]
MAVEN_FILES = ["pom.xml"]
NUGET_FILES = ["packages.config"]
RUBY_FILES = ["Gemfile", "Gemfile.lock"]
CARGO_FILES = ["Cargo.toml", "Cargo.lock"]

ALL_REQUIREMENT_FILES = set(
    PYPI_FILES + NPM_FILES + MAVEN_FILES + NUGET_FILES + RUBY_FILES + CARGO_FILES
)
