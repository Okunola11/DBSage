from fastapi import APIRouter, Depends, Request, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Annotated

from db_sage.app.db.database import get_db
from db_sage.app.v1.services.user import user_service
from db_sage.app.v1.models.user import User
from db_sage.app.utils.success_response import success_response
from db_sage.app.core.dependencies.user import get_current_user
from db_sage.app.v1.schemas.user import (
    RegisterUserRequest,  VerifyUserRequest, EmailRequest, ResetRequest, LoginRequest
)
from db_sage.app.v1.responses.user import (
    RegisterUserResponse, UserLoginResponse, RefreshTokenResponse
    )

auth = APIRouter(prefix="/auth", tags=["Authentication"])

@auth.post("/register", status_code=status.HTTP_201_CREATED, response_model=RegisterUserResponse)
async def register_user(
    data: RegisterUserRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)]
):
    """Register a new user

    Args:
        - data: the request data
        - db: the databases session
        - background_tasks: background task to be called for email service

    Returns:
        - dict: a user response object containing auth tokens and the users data
    """

    return await user_service.create(data, db, background_tasks)

@auth.post("/verify", status_code=status.HTTP_200_OK, response_model=success_response)
async def verify_user_account(
    data: VerifyUserRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)]
):
    """Verifies a registered user's account

    Args:
        - data (VerifyUserRequest): the request data (email and token) for verification
        - db: the database session
        - background_tasks: background task to be called for email service.

    Returns:
       - dict: a success response message
    """

    return await user_service.activate_user_account(data, db, background_tasks)

@auth.post("/login", status_code=status.HTTP_200_OK, response_model=UserLoginResponse)
async def user_login(
    data: LoginRequest,
    db: Annotated[Session, Depends(get_db)]
):
    """Login a user

    Args:
        - data (LoginRequest): request username and password
        - db: the database session

    Returns:
        - dict: the user data with tokens
    """
    
    return await user_service.get_login_token(data, db)

@auth.post("/refresh", status_code=status.HTTP_200_OK, response_model=RefreshTokenResponse)
async def refresh_token(
    db: Annotated[Session, Depends(get_db)],
    request: Request
):
    """Refreshes expired access token

    Args:
        - db:the database session
        - request (Request): request object containing the request cookie

    Returns:
       dict: response message with new tokens
    """

    refresh_token = request.cookies.get("refresh_token")
    return await user_service.get_refresh_token(refresh_token, db)

@auth.post("/forgot-password", status_code=status.HTTP_200_OK, response_model=success_response)
async def forgot_password(
    data: EmailRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)]
):
    """Endpoint for users to request a password change email

    Args:
        - data (EmailRequest): the request data
        - background_tasks: background task for email service
        - db: the database session

    Returns:
        - dict: success message prompting the user to check their mail
    """

    return await user_service.email_forgot_password_link(data, background_tasks, db)

@auth.put("/reset-password", status_code=status.HTTP_200_OK, response_model=success_response)
async def reset_password(
    data: ResetRequest,
    db: Annotated[Session, Depends(get_db)]
):
    """Resets a users password

    Args:
        - data (ResetRequest): the request data
        - db: the database session

    Returns:
        dict: success message upon reset
    """

    return await user_service.reset_user_password(data, db)