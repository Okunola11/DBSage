"""
- Users should be able to generate the login token with a valid refresh token.
- Users should not be able to generate login token with an invalid refresh token.
"""

from tests.conftest import USER_PASSWORD
from app.v1.services.user import user_service

base_url = "/api/v1/auth/refresh"

def test_refresh_token(client, user, test_session):
    tokens = user_service._generate_tokens(user, test_session)
    cookies = {
        "refresh_token": tokens['refresh_token']
    }
    response = client.post(f"{base_url}", cookies=cookies)
    assert response.status_code == 200
    assert 'access_token' in response.json()
    assert 'refresh_token' in response.cookies
    assert response.json()['data'] == {}

def test_refresh_with_invalid_token(client, user, test_session):
    cookies = {
        "refresh_token": "somerandomtoken"
    }
    response = client.post(f"{base_url}", cookies=cookies)
    assert response.status_code == 400
    assert 'access_token' not in response.json()
    assert 'refresh_token' not in response.cookies