from fastapi import APIRouter, Depends, Response, Request, status, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from starlette.responses import RedirectResponse
from authlib.integrations.base_client import OAuthError
from authlib.oauth2.rfc6749 import OAuth2Token
import secrets

from db_sage.app.db.database import get_db
from db_sage.app.core.config.google_oauth_config import google_oauth
from db_sage.app.v1.services.google_oauth import GoogleOAuthService

google_auth = APIRouter(prefix="/auth", tags=["Authentication"])

@google_auth.get("/google")
async def google_oauth2(request: Request) -> RedirectResponse:
    """Allows users to login with their google account
    
    Args:
        request (Request): request object 

    Returns:
        RedirectResponse: a redirect to google's authorization server 
    """
    redirect_uri = request.url_for("google_oauth2_callback")
    # generate a state value and store it in the session
    state = secrets.token_urlsafe(16)
    print(f"STATE IS {state}")
    request.session["state"] = state
    response = await google_oauth.google.authorize_redirect(request, redirect_uri, state=state)
    return response

@google_auth.get("/callback/google")
async def google_oauth2_callback(request: Request, db: Annotated[Session, Depends(get_db)]) -> Response:
    """Handles request from google after user has agreed to authenticate with google account 

    Args:
        request (Request): request object 
        db (Annotated[Session, Depends): database session object 

    Returns:
        Response: contains message, status code, tokens, and user data on success
            Or HttpException if not authenticated 
    """
    try:
        state_in_session = request.session.get("state")
        state_from_params = request.query_params.get("state")
        # verify the state value to prevent CSRF
        if state_in_session != state_from_params: 
            print(f"states not equal; {state_in_session} is not {state_from_params}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="CSRF Warning! State not equal in request and response"
                )
        # get the user access token and information from authorization/resource server
        google_response: OAuth2Token = await google_oauth.google.authorize_access_token(request)
        print(google_response)

        # check if id_token is present
        if "id_token" not in google_response:
            print("id_token not in google_response") 
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Authentication failed")
    except:
        print("Authentication flow failed")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Authentication failed")
    
    try:
        if not google_response.get("access_token"):
            print("no access token in google_response")
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Authentication failed")

        # if google has not verified users email
        if not google_response.get("userinfo", {}).get("email"):
            print("no email in google_response")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Authentication failed")

        # create oauth data for the user 
        google_oauth_service = GoogleOAuthService()
        return google_oauth_service.create(google_response, db)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Exception occured; {exc}")