""" 
- The current authenticated user makes the request, they can update their details.
- Only the current authenticated user or a superadmin can update a user details.
- The user must be verified, active and not deleted.
- The details that can be updated through the endpoint are 'email', 'first_name' and 'last_name'.
- User email cannot be updated to an already existing user email.
"""

from db_sage.app.v1.services.user import user_service
from conftest import USER_FIRSTNAME, USER_LASTNAME

base_url = "/api/v1/users"
data = {
    "email": "changed@email.com",
    "first_name": "tests",
    "last_name": "testing"
}

def test_update_current_user(auth_client, user):
   
    response = auth_client.patch(f"{base_url}", json=data)
    assert response.status_code == 200
    assert response.json()['data']['id'] == user.id
    assert response.json()['data']['email'] == data['email']
    assert response.json()['data']['first_name'] == data['first_name']
    assert response.json()['data']['last_name'] == data['last_name']

def test_update_current_user_with_existing_email(auth_client, inactive_user):
    new_data = {**data, "email": inactive_user.email}
   
    response = auth_client.patch(f"{base_url}", json=new_data)
    assert response.status_code == 400
    assert response.json()['message'] == "Email already taken"

def test_update_current_user_with_null_values(auth_client, inactive_user):
    new_data = {**data, "email": ""}
   
    response = auth_client.patch(f"{base_url}", json=new_data)
    print(response.json())
    assert response.status_code == 422

def test_update_current_user_with_email_only(auth_client, user):
    del data['first_name']
    del data['last_name']
   
    response = auth_client.patch(f"{base_url}", json=data)
    assert response.status_code == 200
    assert response.json()['data']['first_name'] == USER_FIRSTNAME
    assert response.json()['data']['last_name'] == USER_LASTNAME
    assert response.json()['data']['email'] == data['email']

def test_update_current_user_with_invalid_input(auth_client):
    new_data = {**data, "first_name": 999}

    response = auth_client.patch(f"{base_url}", json=new_data)
    print(response.json())
    assert response.status_code == 422

def test_update_current_user_with_inactive_user(client, inactive_user, test_session):
    tokens = user_service._generate_tokens(inactive_user, test_session)
    headers = {
        "Authorization": f"Bearer {tokens['access_token']}"
    }
    response = client.patch(f"{base_url}", headers=headers, json=data)
    assert response.status_code == 400
    assert response.json()['message'] == "User is inactive and cannot be updated"

def test_update_current_user_with_unverified_user(client, unverified_user, test_session):
    tokens = user_service._generate_tokens(unverified_user, test_session)
    headers = {
        "Authorization": f"Bearer {tokens['access_token']}"
    }
    response = client.patch(f"{base_url}", headers=headers, json=data)
    assert response.status_code == 400
    assert response.json()['message'] == "User is not verified and cannot be updated"

def test_update_current_user_with_deleted_user(client, deleted_user, test_session):
    tokens = user_service._generate_tokens(deleted_user, test_session)
    headers = {
        "Authorization": f"Bearer {tokens['access_token']}"
    }
    response = client.patch(f"{base_url}", headers=headers, json=data)
    assert response.status_code == 400
    assert response.json()['message'] == "User is deleted and cannot be updated"

def test_update_current_user_with_unauthenticated_user(client):
    
    response = client.patch(f"{base_url}", json=data)
    print(response.json())
    assert response.status_code == 401
    assert response.json()['message'] == "Not authenticated"

def test_update_current_user_with_unauthorized_user(client):
    
    response = client.patch(f"{base_url}", json=data, headers={"Authorization": "Bearer eyjal09lk390jo3e"})
    print(response.json())
    assert response.status_code == 401
    assert response.json()['message'] == "Not authorized"