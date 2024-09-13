""" 
- Only superadmins can fetch all users.
- Page and per_page parameters can be used for pagination.
- Filters ['is_superadmin', 'is_active', 'is_verified', 'is_deleted'] can be used as params also.
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

def test_fetch_users_with_superadmin(client, user, inactive_user, superadmin_header):   
    response = client.get(f"{base_url}", headers=superadmin_header)
    assert response.status_code == 200
    assert response.json()['total'] == 3
    assert user.email in [usr['email'] for usr in response.json()['data']]
    assert inactive_user.email in [usr['email'] for usr in response.json()['data']]
    
def test_fetch_users_with_non_superadmin(client, user, test_session):
    tokens = user_service._generate_tokens(user, test_session)
    headers = {
        "Authorization": f"Bearer {tokens['access_token']}"
    }

    response = client.get(f"{base_url}", headers=headers)
    assert response.status_code == 403
    assert response.json()['message'] == "You do not have permission!"

def test_fetch_users_with_pagination_param(client, superadmin_header, user, inactive_user, deleted_user):   
    response = client.get(f"{base_url}?page=2&per_page=1", headers=superadmin_header)
    assert response.status_code == 200
    assert response.json()['total'] == 1
    assert response.json()['per_page'] == 1
    assert user.email in [usr['email'] for usr in response.json()['data']]

    response = client.get(f"{base_url}?page=3&per_page=1", headers=superadmin_header)
    assert response.status_code == 200
    assert response.json()['total'] == 1
    assert response.json()['per_page'] == 1
    assert inactive_user.email in [usr['email'] for usr in response.json()['data']]

    response = client.get(f"{base_url}?page=4&per_page=1", headers=superadmin_header)
    assert response.status_code == 200
    assert response.json()['total'] == 1
    assert response.json()['per_page'] == 1
    assert deleted_user.email in [usr['email'] for usr in response.json()['data']]

def test_fetch_users_with_non_boolean_filters(client, superadmin_header, user, inactive_user, deleted_user):   
    response = client.get(f"{base_url}?is_superadmin=nay", headers=superadmin_header)
    assert response.status_code == 422

def test_fetch_users_with_filters(client, superadmin_header, superadmin, user, inactive_user, deleted_user, unverified_user):
    response = client.get(f"{base_url}?is_superadmin=true", headers=superadmin_header)
    assert response.status_code == 200
    assert response.json()['total'] == 1
    assert superadmin.email in [usr['email'] for usr in response.json()['data']]
    assert all(email not in [usr['email'] for usr in response.json()['data']] for email in (
        user.email,
        inactive_user.email,
        deleted_user.email,
        unverified_user.last_name,
    ))

    response = client.get(f"{base_url}?is_superadmin=false", headers=superadmin_header)
    assert response.status_code == 200
    assert response.json()['total'] == 4
    assert superadmin.email not in [usr['email'] for usr in response.json()['data']]
    assert all(email in [usr['email'] for usr in response.json()['data']] for email in (
        user.email,
        inactive_user.email,
        deleted_user.email,
        unverified_user.email
    ))

    response = client.get(f"{base_url}?is_superadmin=false&is_deleted=true", headers=superadmin_header)
    assert response.status_code == 200
    assert response.json()['total'] == 1
    assert deleted_user.email in [usr['email'] for usr in response.json()['data']]
    assert all(email not in [usr['email'] for usr in response.json()['data']] for email in (
        superadmin.email,
        user.email,
        inactive_user.email,
        unverified_user.email
    ))

def test_fetch_with_filters_to_return_no_user(
    client, superadmin_header, superadmin, user,
    inactive_user, deleted_user, unverified_user
    ):
    response = client.get(f"{base_url}?is_superadmin=true&is_active=false&is_deleted=true", headers=superadmin_header)
    assert response.status_code == 200
    assert response.json()['message'] == "No User(s) found"
    assert response.json()['total'] == 0
    assert response.json()['data'] == []


   