from enum import Enum


class Manager(str, Enum):
    rubygems = "rubygems"
    cargo = "cargo"
    nuget = "nuget"
    pypi = "pypi"
    npm = "npm"
    maven = "maven"
