from enum import Enum


class Manager(str, Enum):
    cargo = "cargo"
    nuget = "nuget"
    pypi = "pypi"
    npm = "npm"
    maven = "maven"
