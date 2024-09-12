"""
- Test if the user account action is working
- Test activation link is valid only once
- Test activation link is not allowing invalid token
- Test activation link is not allowing invalid email
"""

import time
from app.core.config.security import hash_password
from app.v1.models.user import User
from app.utils.email_context import USER_VERIFY_ACCOUNT

base_url = "/api/v1/auth/verify"

def test_user_account_verification(client, unverified_user, test_session):
    token_context = unverified_user.get_context_string(USER_VERIFY_ACCOUNT)
    token = hash_password(token_context)
    data = {
        "email": unverified_user.email,
        "token": token
    }
    response = client.post(f"{base_url}", json=data)
    assert response.status_code == 200
    activated_user = test_session.query(User).filter_by(email = unverified_user.email).first()
    assert activated_user.is_verified == True
    assert activated_user.is_active == True
    assert activated_user.verified_at is not None

def test_user_link_does_not_work_twice(client, unverified_user, test_session):
    token_context = unverified_user.get_context_string(USER_VERIFY_ACCOUNT)
    token = hash_password(token_context)
    data = {
    "email": unverified_user.email,
    "token": token
    }
    response = client.post(f"{base_url}", json=data)
    assert response.status_code == 200
    # the user account is activated now
    # now we test attempt to make another call, it should not work
    response = client.post(f"{base_url}", json=data)
    assert response.status_code != 200
    assert response.status_code == 400
    assert response.json()['message'] == "This link is either expired or not valid"

def test_user_invalid_token_does_not_work(client, unverified_user, test_session):
    data = {
        "email": unverified_user.email,
        "token": "somerandomnonexistingtoken"
    }
    response = client.post(f"{base_url}", json=data)
    assert response.status_code == 400
    assert response.json()['message'] == "This link is either expired or not valid"
    activated_user = test_session.query(User).filter_by(email = unverified_user.email).first()
    assert activated_user.is_active is False
    assert activated_user.verified_at is None

def test_user_invalid_email_does_not_work(client, unverified_user, test_session):
    token_context = unverified_user.get_context_string(USER_VERIFY_ACCOUNT)
    token = hash_password(token_context)
    data = {
        "email": "some@random.com",
        "token": token
    }
    response = client.post(f"{base_url}", json=data)
    assert response.status_code == 400
    assert response.json()['message'] == "This link is not valid"
    activated_user = test_session.query(User).filter_by(email = unverified_user.email).first()
    assert activated_user.is_active is False
    assert activated_user.verified_at is None