from typing import Annotated

from fastapi import APIRouter, Body, Depends, status
from fastapi.responses import JSONResponse

from app.models import (
    AccountExistsRequest,
    ChangePasswordRequest,
    LoginRequest,
    User,
    VerifyAccessTokenRequest,
)
from app.services import (
    create_user,
    read_user_by_email,
    update_user_password,
)
from app.utils import (
    JWTBearer,
    create_access_token,
    get_hashed_password,
    json_encoder,
    verify_access_token,
    verify_password,
)

router = APIRouter()

@router.post("/auth/signup")
async def signup(user: User) -> JSONResponse:
    existing_user = await read_user_by_email(user.email)
    if existing_user:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=json_encoder(
                {"message": "user_already_exists"}
            ),
        )
    await create_user({
        "email": user.email,
        "password": await get_hashed_password(user.password),
        "repositories": []
    })
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder(
            {"message": "success"}
        ),
    )


@router.post("/auth/login")
async def login(login_request: Annotated[LoginRequest, Body()]) -> JSONResponse:
    user = await read_user_by_email(login_request.email)
    if user is None:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=json_encoder(
                {"message": "user_no_exist"}
            ),
        )
    hashed_pass = user["password"]
    if not await verify_password(login_request.password, hashed_pass):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=json_encoder(
                {"message": "Incorrect password"}
            ),
        )
    access_token = await create_access_token(user["_id"])
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder(
            {
                "access_token": access_token,
                "user_id": user["_id"],
                "message": "success"
            }
        ),
    )


@router.post("/auth/account_exists")
async def account_exists(account_exists_request: AccountExistsRequest) -> JSONResponse:
    user = await read_user_by_email(account_exists_request.email)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder({"userExists": True if user else False}),
    )


@router.post("/auth/verify_token")
async def verify_token(verify_access_token_request: VerifyAccessTokenRequest) -> JSONResponse:
    valid = (
        verify_access_token(verify_access_token_request.access_token)
        if verify_access_token_request.access_token else False
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder({"valid": valid}),
    )


@router.post("/auth/change_password", dependencies=[Depends(JWTBearer())], tags=["auth"])
async def change_password(change_password_request: ChangePasswordRequest) -> JSONResponse:
    user = await read_user_by_email(change_password_request.email)
    if user is None:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=json_encoder(
                {"message": f"User with email {change_password_request.email} don't exist"}
            ),
        )
    if not await verify_password(change_password_request.old_password, user["password"]):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=json_encoder(
                {"message": "Invalid old password"}
            ),
        )
    encrypted_password = await get_hashed_password(change_password_request.new_password)
    user["password"] = encrypted_password
    await update_user_password(user)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder(
            {"message": "Password changed successfully"}
        ),
    )
