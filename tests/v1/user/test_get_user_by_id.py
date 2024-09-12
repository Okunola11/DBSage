""" 
- Only an authenticated superadmin can fetch any user by ID
"""

from app.v1.services.user import user_service

base_url = "/api/v1/users"

def test_fetch_user_by_id_with_superadmin(client, user, superadmin, test_session):
    data = user_service._generate_tokens(superadmin, test_session)
    headers = {
        "Authorization": f"Bearer {data['access_token']}"
    }
    response = client.get(f"{base_url}/{user.id}", headers=headers)
    assert response.status_code == 200
    assert response.json()['data']['email'] == user.email
    assert response.json()['data']['id'] == user.id

def test_fetch_user_by_id_with_non_superadmin(client, user, superadmin, test_session):
    data = user_service._generate_tokens(user, test_session)
    headers = {
        "Authorization": f"Bearer {data['access_token']}"
    }
    response = client.get(f"{base_url}/{user.id}", headers=headers)
    assert response.status_code == 403
    assert response.json()['message'] == "You do not have permission!"

def test_fetch_user_by_id_with_invalid_token(client, user, test_session):
    data = user_service._generate_tokens(user, test_session)
    headers = {
        "Authorization": f"Bearer {data['access_token'][:-6]}gpc"
    }
    response = client.get(f"{base_url}/{user.id}", headers=headers)
    print(response.json())
    assert response.status_code == 401
    assert response.json()['message'] == "Not authorized"