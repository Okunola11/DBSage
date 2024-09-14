from typing import Annotated
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from db_sage.app.db.database import get_db
from db_sage.app.core.config.security import get_token_user
from db_sage.app.v1.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Annotated[Session, Depends(get_db)]):
    """Gets the current authenticated user

    Args:
        - token: the users access token
        - db: the database session

    raises:
        - HTTPException: 401 for unvalidated credentials

    Returns:
        dict: the current user obj if successful
    """

    user = await get_token_user(token, db)

    if user:
        return user

    raise HTTPException(status_code=401, detail="Not authorized")

async def get_current_active_user(
    token: Annotated[str, Depends(oauth2_scheme)], 
    db: Annotated[Session, Depends(get_db)]
    ):
    """Gets the current active authenticated user

    Args:
        - token: the users access token
        - db: the database session

    raises:
        - HTTPException: 401 for unvalidated credentials

    Returns:
        dict: the current user obj if successful
    """

    user: User = await get_token_user(token, db)

    if (user) and (user.is_active):
        return user

    raise HTTPException(status_code=401, detail="Not authorized")

async def get_current_superadmin(token: Annotated[str, Depends(oauth2_scheme)], db: Annotated[Session, Depends(get_db)]):
    """Checks if the current authenticated user is a superadmin

    Args:
        - token: the users access token
        - db: the database session

    Raises:
        - HTTPException: 401 is the user is not authenticated
        - HTTPException: 403 if the authenticated user is not a superadmin

    Returns:
        dict: the current user obj if successful
    """
    
    user: User = await get_current_active_user(token, db)

    if user.is_superadmin:
        return user

    raise HTTPException(status_code=403, detail="You do not have permission!")