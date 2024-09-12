from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import Annotated, Optional

from db_sage.app.db.database import get_db
from db_sage.app.v1.services.user import user_service
from db_sage.app.v1.models.user import User
from db_sage.app.core.dependencies.user import get_current_user, get_current_superadmin
from db_sage.app.v1.schemas.user import UpdateUserRequest
from db_sage.app.v1.responses.user import FetchUserResponse, FetchAllUsersResponse

user_router = APIRouter(prefix="/users", tags=["Users"])

@user_router.get("/me", status_code=status.HTTP_200_OK, response_model=FetchUserResponse)
async def get_current_user_details(user: Annotated[User, Depends(get_current_user)]):
    """Endpoint to fetch the current authenticated user details

    Args:
        user: the current authenticated user

    Returns:
        dict: the user obj
    """

    return user_service.fetch_me(user)

@user_router.get("/{user_id}", status_code=status.HTTP_200_OK, response_model=FetchUserResponse)
def get_user_by_id(
    user_id: Annotated[str, "ID of the user to fetch"],
    user: Annotated[User, Depends(get_current_superadmin)],
    db: Annotated[Session, Depends(get_db)]
):
    """Endpoint for superadmin to get a user by ID

    Args:
        - user_id: the user ID to fetch
        - user: the current authenticated superadmin
        - db: the database session.

    Raises:
        - HTTPException: 404 for non-existing request ID
        - HTTPException: 403 for requests by non superadmin

    Returns:
        dict: user obj
    """

    return user_service.fetch(db, user_id)

@user_router.patch("", status_code=status.HTTP_200_OK, response_model=FetchUserResponse)
def update_current_user(
    data: Annotated[UpdateUserRequest, "User must be verified, active and not deleted"],
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """Endpoint for the current authenticated user to update their details

    Args:
        - data: update request data. User must be verified, active and not deleted.
        - user: the current user
        - db: the database session.

    Returns:
        dict: updated user obj
    """

    return user_service.update(db, user, data)

@user_router.patch("/{user_id}", status_code=status.HTTP_200_OK, response_model=FetchUserResponse)
def update_user(
    user_id: Annotated[str, "ID of the user to update"],
    data: Annotated[UpdateUserRequest, "User must be verified, active and not deleted"],
    user: Annotated[User, Depends(get_current_superadmin)],
    db: Annotated[Session, Depends(get_db)]
):
    """Endpoint for superadmin to update a users detail

    Args:
        - user_id: id of the user to update
        - data: update request data. User must be verified, active and not deleted.
        - user: the current user
        - db: the database session.

    Returns:
        dict: updated user obj
    """

    return user_service.update(db, user, data, user_id)

@user_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: Annotated[str, "ID of the user to delete"],
    user: Annotated[User, Depends(get_current_superadmin)],
    db: Annotated[Session, Depends(get_db)]
):
    """Endpoint to soft delete a user

    Args:
        - user_id: ID of the user to delete
        - user: the current authenticated superadmin
        - db: the database session

    Raises:
        - HTTPException: 404 for invalid user_id
        - HTTPException: 403 for authenticated users who are not superadmins
        - HTTPException: 401 for unauthenticated users
        - HTTPException: 409 for already deleted users
        - HTTPException: 400 for requests by non superadmin whose request ID do not match their ID
    """
    
    return user_service.delete(db, user, user_id)

@user_router.get("", status_code=status.HTTP_200_OK, response_model=FetchAllUsersResponse)
def get_all_users(
    user: Annotated[User, Depends(get_current_superadmin)],
    db: Annotated[Session, Depends(get_db)],
    page: Annotated[int, Query(ge=1, description="Page Number (starts from 1)")] = 1,
    per_page: Annotated[int, Query(ge=1, description="Number of users per page")] = 10,
    is_active: Annotated[Optional[bool], Query()] = None,
    is_verified: Annotated[Optional[bool], Query()] = None,
    is_deleted: Annotated[Optional[bool], Query()] = None,
    is_superadmin: Annotated[Optional[bool], Query()] = None
):
    """Endpoint for superadmin to retrieve all users

    Args:
        - user: the current authenticated superadmin
        - db: the database session
        - page: current page parameter
        - per_page: number of data per page parameter
        - is_active: boolean to filter active users
        - is_verified: boolean to filter verified users
        - is_deleted: boolean to filter deleted users
        - is_superadmin: boolean to filter users that are superadmins

    Returns:
        dict: response obj with users data if available
    """

    query_params = {
        "is_active": is_active,
        "is_verified": is_verified,
        "is_deleted": is_deleted,
        "is_superadmin": is_superadmin
    }
    return user_service.fetch_all(db, page, per_page, **query_params)