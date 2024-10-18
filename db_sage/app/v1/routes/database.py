from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated

from db_sage.app.db.database import get_db
from db_sage.app.core.dependencies.user import get_current_active_user
from db_sage.app.v1.models import User
from db_sage.app.v1.schemas.database import DatabaseUrl
from db_sage.app.core.config.db import DatabaseStateManager
from db_sage.app.utils.success_response import success_response

database_connection_router = APIRouter(prefix="/database", tags=["Database"])

@database_connection_router.post("/connect", status_code=status.HTTP_200_OK, response_model=success_response)
async def connect_database(
    data: DatabaseUrl,
    user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Establish a connection to a database using the provided URL.

    This endpoint attempts to connect to a database using the URL provided in the request body.
    If successful, it retrieves and returns information about all tables and their columns in the database.
    Only authenticated and active users can access this endpoint.

    Args:
        data (DatabaseUrl): A Pydantic model containing the database URL.
        user (User): The current authenticated user, injected by FastAPI.

    Returns:
        dict: A success response containing:
            - status_code (int): HTTP status code (200 for success).
            - message (str): A success message.
            - data (list): List of dictionaries, each containing table name and its columns.

    Raises:
        HTTPException: 
            - 500 status code if the database connection fails.
            - Any authentication-related exceptions from the `get_current_active_user` dependency.

    Note:
        This function uses a DatabaseStateManager to manage the database connection state.
        The actual database operations are performed using a separate database connection object.
    """

    db_url = data.db_url

    db_state = DatabaseStateManager()
    if db_state.set_connection(db_url):
        db = db_state.get_connection()
        tables_and_columns = db.get_all_tables_and_columns()
        return success_response(
            status_code=200,
            message="Database connection established successfully.",
            data=tables_and_columns
        )
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database connection failed.")


@database_connection_router.post("/close", status_code=status.HTTP_200_OK, response_model=success_response)
async def close_database_connection(
    user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Close the current database connection.

    This endpoint attempts to close the current active database connection.
    It can be used to manually release database resources when they are no longer needed.
    Only authenticated and active users can access this endpoint.

    Args:
        user (User): The current authenticated user, injected by FastAPI.

    Returns:
        dict: A success response containing:
            - status_code (int): HTTP status code (200 for success).
            - message (str): A success message indicating the connection was closed.

    Raises:
        HTTPException: 
            - 404 status code if no active database connection exists.
            - Any authentication-related exceptions from the `get_current_active_user` dependency.

    Note:
        This function uses a DatabaseStateManager to manage the database connection state.
        After closing the connection, any attempts to use the database will require
        re-establishing a connection.
    """

    db_state = DatabaseStateManager()
    if db_state.get_connection() is not None:
        db_state.close_connection()
        return success_response(
            status_code=200,
            message="Database connection closed successfully.",
        )
    else:
        raise HTTPException(status_code=404, detail="No active database connection found.")


@database_connection_router.get("/tables", status_code=status.HTTP_200_OK, response_model=success_response)
async def get_tables(
    user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Retrieve all database tables and their columns for the current user.

    This endpoint fetches a list of all tables and their respective columns
    from the connected database. It checks if there is an active database
    connection, and if so, returns the tables and columns in a successful response.
    
    If no active connection is found, an HTTP 404 error is raised.

    Args:
        user (User): The currently authenticated user, fetched via the `get_current_active_user` dependency.

    Returns:
        success_response (dict): A JSON object containing the status code, 
        a success message, and the list of tables with their columns from the database.

    Raises:
        HTTPException (404): If there is no active database connection.
    """
    
    db_state = DatabaseStateManager()
    if db_state.get_connection() is not None:
        db = db_state.get_connection()
        tables_and_columns = db.get_all_tables_and_columns()
        return success_response(
            status_code=200,
            message="Database tables generated successfully.",
            data=tables_and_columns
        )
    else:
        raise HTTPException(status_code=404, detail="No active database connection found.")