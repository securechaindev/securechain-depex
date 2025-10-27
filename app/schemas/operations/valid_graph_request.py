from pydantic import Field

from app.schemas.base_schema import BaseSchemaWithMaxDepth
from app.schemas.enums import NodeType
from app.schemas.patterns import NEO4J_ID_PATTERN


class ValidGraphRequest(BaseSchemaWithMaxDepth):
    requirement_file_id: str = Field(
        pattern=NEO4J_ID_PATTERN
    )
    max_depth: int = Field(...)
    node_type: NodeType
