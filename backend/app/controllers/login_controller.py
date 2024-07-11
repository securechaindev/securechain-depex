from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Body, status
from fastapi.responses import JSONResponse

from app.models import AccountExistsRequest, ChangePasswordRequest, LoginRequest, User
from app.services import (
    create_jwt_token,
    create_user,
    read_user_by_email,
    update_user_password,
)
from app.utils import (
    create_access_token,
    get_hashed_password,
    json_encoder,
    verify_password,
)

ALGORITHM = "HS256"
JWT_SECRET_KEY = "narscbjim@$@&^@&%^&RFghgjvbdsha"   # should be kept secret
JWT_REFRESH_SECRET_KEY = "13ugfdfgh@#$%^@&jkl45678902"

router = APIRouter()

@router.post("/user/signup")
async def signup(user: User):
    existing_user = await read_user_by_email(user.email)
    if existing_user:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=json_encoder(
                {"message": "user_already_exists"}
            ),
        )

    encrypted_password = await get_hashed_password(user.password)
    user.password = encrypted_password

    await create_user({
        "email": user.email,
        "password": user.password,
        "repositories": []
    })

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder(
            {"message": "success"}
        ),
    )


@router.post("/user/login")
async def login(login_request: Annotated[LoginRequest, Body()]):
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
    await create_jwt_token(
        token = {
            "user": user["_id"],
            "access_token": access_token,
            "status": True,
            "moment": datetime.now()
        }
    )

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


@router.post('/user/account_exists')
async def account_exists(account_exists_request: AccountExistsRequest):
    user = await read_user_by_email(account_exists_request.email)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder({"userExists": True if user else False}),
    )


@router.post('/user/change_password')
async def change_password(change_password_request: ChangePasswordRequest):
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


# @router.post('/user/logout')
# def logout(dependencies=Depends(JWTBearer())):
#     token=dependencies
#     payload = jwt.decode(token, JWT_SECRET_KEY, ALGORITHM)
#     user_id = payload['sub']

#     existing_token = db.query(models.TokenTable).filter(models.TokenTable.user_id == user_id, models.TokenTable.access_toke==token).first()
#     if existing_token:
#         existing_token.status=False
#         db.add(existing_token)
#         db.commit()
#         db.refresh(existing_token)
#     return {"message":"Logout Successfully"}


# def token_required(func):
#     @wraps(func)
#     def wrapper(*args, **kwargs):

#         payload = jwt.decode(kwargs['dependencies'], JWT_SECRET_KEY, ALGORITHM)
#         user_id = payload['sub']
#         data = kwargs['session'].query(models.TokenTable).filter_by(user_id=user_id,access_toke=kwargs['dependencies'],status=True).first()
#         if data:
#             return func(kwargs['dependencies'],kwargs['session'])
#         else:
#             return {'msg': "Token blocked"}

#     return wrapper
