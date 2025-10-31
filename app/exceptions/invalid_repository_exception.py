from fastapi import HTTPException


class InvalidRepositoryException(HTTPException):
    def __init__(self, owner: str, name: str):
        super().__init__(
            status_code=404,
            detail={"code": "repository_not_found", "message": f"Repository {name} not found for owner {owner} "}
        )
