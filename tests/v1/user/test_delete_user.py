""" 
- Only superadmins can deleted a user.
- Accounts are to be soft deleted.
- Superadmins cannot delete and already deleted account.
"""

import pytest

from db_sage.app.v1.services.user import user_service

base_url = "/api/v1/users"

@pytest.fixture
def superadmin_header(superadmin, test_session):
    tokens = user_service._generate_tokens(superadmin, test_session)
    return {
        "Authorization": f"Bearer {tokens['access_token']}"
    }

def test_delete_user_with_superadmin(client, user, superadmin_header):   
    response = client.delete(f"{base_url}/{user.id}", headers=superadmin_header)
    assert response.status_code == 204
    assert user.is_active == False
    assert user.is_deleted == True
    
def test_delete_user_with_non_superadmin(client, user, test_session):
    tokens = user_service._generate_tokens(user, test_session)
    headers = {
        "Authorization": f"Bearer {tokens['access_token']}"
    }

    response = client.delete(f"{base_url}/{user.id}", headers=headers)
    assert response.status_code == 403
    assert response.json()['message'] == "You do not have permission!"

def test_delete_user_with_deleted_user_id(client, superadmin_header, deleted_user):   
    response = client.delete(f"{base_url}/{deleted_user.id}", headers=superadmin_header)
    assert response.status_code == 409
    assert response.json()['message'] == "User is already deleted"
