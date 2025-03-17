from enum import Enum


class Manager(str, Enum):
    rubygems = "RubyGems"
    cargo = "Cargo"
    nuget = "NuGet"
    pypi = "PyPI"
    npm = "NPM"
    maven = "Maven"
