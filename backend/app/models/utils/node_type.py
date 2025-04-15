from enum import Enum


class NodeType(str, Enum):
    rubygems_package = "RubyGemsPackage"
    cargo_package = "CargoPackage"
    nuget_package = "NuGetPackage"
    pypi_package = "PyPIPackage"
    npm_package = "NPMPackage"
    maven_package = "MavenPackage"
