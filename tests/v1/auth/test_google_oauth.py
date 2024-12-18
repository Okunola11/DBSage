import pytest
import asyncio
from starlette.responses import RedirectResponse

from db_sage.app.v1.models.user import User
from db_sage.app.v1.models.oauth import OAuth
from db_sage.app.core.config.google_oauth_config import google_oauth
from db_sage.app.v1.services.google_oauth import GoogleOAuthService

return_value = {
    'access_token': 'zz-some-random-token', 
    'scope': 'openid https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email', 
    'token_type': 'Bearer', 
    'id_token': 'zz-some-random-token', 
    'expires_at': 1723326936, 
    'userinfo': {
        'iss': 'https://accounts.google.com', 
        'azp': '2526346346346-23452355555555555555.apps.googleusercontent.com', 
        'aud': '2532525625-25234222222222.apps.googleusercontent.com', 
        'sub': '454635346464736352535', 
        'email': 'testing@gmail.com', 
        'email_verified': True, 
        'at_hash': 'afaerdesdfad', 
        'nonce': 'adfasdfafafda', 
        'name': 'John Doe', 
        'picture': 'https://lh3.googleusercontent.com/a/ACg8ocI4CTuHC1Yy790aYH6zRvr8rj0l7R5JtBgNoYmK1q-dg1dJxA=s96-c', 
        'given_name': 'John', 
        'family_name': 'Doe', 
        'iat': 90909090909, 
        'exp': 909090990909}}

generate_token_return = {
    "access_token": "some_random_toknee",
    "refresh_token": "some_random_token"
}

# mock the authorize_redirect and authorize_access_token attributes of google oauth
@pytest.fixture()
def mock_google_oauth2(monkeypatch):
    async def mock_authorize_redirect(*args, **kwargs):
        state = kwargs.get("state")
        return RedirectResponse(url=f"/api/v1/auth/callback/google?state={state}")
        
    async def mock_authorize_token_userinfo(*args):
        return return_value

    monkeypatch.setattr(google_oauth.google, "authorize_redirect", mock_authorize_redirect)
    monkeypatch.setattr(google_oauth.google, "authorize_access_token", mock_authorize_token_userinfo)
    monkeypatch.setattr(GoogleOAuthService, "get_response", lambda self, *args: generate_token_return)

# Test google login flow and database flow after login
def test_google_login(client, test_session, mock_google_oauth2):
    response = client.get("/api/v1/auth/google")

    assert response.status_code == 200
    assert response.json()['access_token'] == generate_token_return['access_token']