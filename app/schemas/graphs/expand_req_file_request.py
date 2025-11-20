from pydantic import BaseModel, Field

from app.schemas.patterns import NEO4J_ID_PATTERN


class ExpandReqFileRequest(BaseModel):
    requirement_file_id: str = Field(
        ...,
        pattern=NEO4J_ID_PATTERN,
        description="Requirement file ID following the Neo4j ID pattern"
    )
