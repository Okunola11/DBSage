""" 
- Only a superadmin can update users details using this endpoint.
- The user to be updated must be verified, active and not deleted.
- Non existing users cannot be updated.
- The details that can be updated through the endpoint are 'email', 'first_name' and 'last_name'.
- User email cannot be updated to an already existing user email.
"""

import pytest

from db_sage.app.v1.services.user import user_service
from conftest import USER_FIRSTNAME, USER_LASTNAME

base_url = "/api/v1/users"
data = {
    "email": "changed@email.com",
    "first_name": "tests",
    "last_name": "testing"
}

@pytest.fixture
def superadmin_header(superadmin, test_session):
    tokens = user_service._generate_tokens(superadmin, test_session)
    return {
        "Authorization": f"Bearer {tokens['access_token']}"
    }

def test_update_user_with_superadmin(client, user, superadmin_header):   
    response = client.patch(f"{base_url}/{user.id}", headers=superadmin_header, json=data)
    assert response.status_code == 200
    assert response.json()['data']['id'] == user.id
    assert response.json()['data']['email'] == data['email']
    assert user.first_name is not USER_FIRSTNAME
    assert user.last_name is not USER_LASTNAME

def test_update_user_with_non_superadmin(client, user, test_session):
    tokens = user_service._generate_tokens(user, test_session)
    headers = {
        "Authorization": f"Bearer {tokens['access_token']}"
    }

    response = client.patch(f"{base_url}/{user.id}", headers=headers, json=data)
    assert response.status_code == 403
    assert response.json()['message'] == "You do not have permission!"

def test_update_user_with_non_existing_user(client, superadmin_header):
    response = client.patch(f"{base_url}/393nlkdj393", headers=superadmin_header, json=data)
    assert response.status_code == 404
    assert response.json()['message'] == "User does not exist"

def test_update_user_with_existing_email(client, superadmin_header, user, inactive_user):
    new_data = {**data, "email": inactive_user.email}
   
    response = client.patch(f"{base_url}/{user.id}", headers=superadmin_header, json=new_data)
    assert response.status_code == 400
    assert response.json()['message'] == "Email already taken"


def test_update_user_with_inactive_user(client, inactive_user, superadmin_header):
    response = client.patch(f"{base_url}/{inactive_user.id}", headers=superadmin_header, json=data)
    assert response.status_code == 400
    assert response.json()['message'] == "User is inactive and cannot be updated"

def test_update_user_with_unverified_user(client, unverified_user, superadmin_header):
    response = client.patch(f"{base_url}/{unverified_user.id}", headers=superadmin_header, json=data)
    assert response.status_code == 400
    assert response.json()['message'] == "User is not verified and cannot be updated"

def test_update_user_with_deleted_user(client, deleted_user, superadmin_header):
    response = client.patch(f"{base_url}/{deleted_user.id}", headers=superadmin_header, json=data)
    assert response.status_code == 400
    assert response.json()['message'] == "User is deleted and cannot be updated"

def test_update_user_with_unauthenticated_user(client, user):
    
    response = client.patch(f"{base_url}/{user.id}", json=data)
    assert response.status_code == 401
    assert response.json()['message'] == "Not authenticated"