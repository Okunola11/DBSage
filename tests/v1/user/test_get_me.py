""" 
- Authenticated users should be able to fetch their own details
"""

from db_sage.app.v1.services.user import user_service

base_url = "/api/v1/users/me"

def test_fetch_me(client, user, test_session):
    data = user_service._generate_tokens(user, test_session)
    headers = {
        "Authorization": f"Bearer {data['access_token']}"
    }
    response = client.get(f"{base_url}", headers=headers)
    assert response.status_code == 200
    assert response.json()['data']['email'] == user.email

def test_fetch_me_with_invalid_token(client, user, test_session):
    data = user_service._generate_tokens(user, test_session)
    headers = {
        "Authorization": f"Bearer {data['access_token'][:-6]}gpc"
    }
    response = client.get(f"{base_url}", headers=headers)
    assert response.status_code == 401
    assert user.email not in response.json()
    assert user.id not in response.json()