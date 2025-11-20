from typing import ClassVar

from app.logger import logger
from app.schemas.enums import Manager, NodeType


class ManagerNodeTypeMapper:
    MAPPING: ClassVar[dict[Manager, NodeType]] = {
        Manager.pypi: NodeType.pypi_package,
        Manager.npm: NodeType.npm_package,
        Manager.maven: NodeType.maven_package,
        Manager.nuget: NodeType.nuget_package,
        Manager.cargo: NodeType.cargo_package,
        Manager.rubygems: NodeType.rubygems_package,
    }

    @classmethod
    def manager_to_node_type(cls, manager: str) -> str | None:
        try:
            manager_enum = Manager(manager)
            return cls.MAPPING[manager_enum].value
        except (ValueError, KeyError):
            logger.warning(f"Unknown or unsupported manager: {manager}")
            return None
