import pytest
import asyncio
from starlette.responses import RedirectResponse

from app.v1.models.user import User
from app.v1.models.oauth import OAuth
from app.core.config.google_oauth_config import google_oauth

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

# Test google login flow and database flow after login
def test_google_login(client, test_session, mock_google_oauth2):
    response = client.get("/api/v1/auth/google")

    assert response.status_code == 200
    assert response.json()['tokens']['token_type'] == 'bearer'
    assert response.json()['user']['email'] == return_value['userinfo']['email']
    assert response.json()['user']['first_name'] == return_value['userinfo']['given_name']
    assert response.json()['user']['last_name'] == return_value['userinfo']['family_name']

    # test user is saved to db and the oauth data is saved
    user_id = response.json()['user']['id']
    user = test_session.query(User).filter_by(id=user_id).first()

    assert user.first_name == return_value['userinfo']['given_name']
    assert user.email == return_value['userinfo']['email']

    # test for oauth data
    oauth = test_session.query(OAuth).filter_by(user_id=user_id).first()

    assert oauth.access_token == return_value['access_token']
    assert oauth.refresh_token == ''
    assert oauth.sub == return_value['userinfo']['sub']