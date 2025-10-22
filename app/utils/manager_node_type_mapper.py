from typing import ClassVar

from app.schemas.enums import Manager, NodeType


class ManagerNodeTypeMapper:
    _MAPPING: ClassVar[dict[Manager, NodeType]] = {
        Manager.pypi: NodeType.pypi_package,
        Manager.npm: NodeType.npm_package,
        Manager.maven: NodeType.maven_package,
        Manager.nuget: NodeType.nuget_package,
        Manager.cargo: NodeType.cargo_package,
        Manager.rubygems: NodeType.rubygems_package,
    }

    @classmethod
    def manager_to_node_type(cls, manager: str) -> str:
        try:
            manager_enum = Manager(manager)
            return cls._MAPPING[manager_enum].value
        except (ValueError, KeyError):
            return NodeType.pypi_package.value
