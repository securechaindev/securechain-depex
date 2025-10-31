from fastapi import HTTPException


class DateNotFoundException(HTTPException):
    def __init__(self, owner: str, name: str):
        super().__init__(
            status_code=404,
            detail={
                "code": "date_not_found",
                "message": f"Last commit date not found in repository {name} for owner {owner}"
            }
        )
