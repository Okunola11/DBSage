"""
- Users should be able to reset his password with combination of a valid token and a valid email
- Users should not be able to reset password with an invalid token
- Users should not be able to reset password with an invalid email
- Users should no the able to rest password with an invalid email and valid token
- Users should not be able to reset password with an invalid new password
"""

from db_sage.app.core.config.security import hash_password
from db_sage.app.utils.email_context import FORGOT_PASSWORD

base_url = "/api/v1/auth/reset-password"
login_url = "/api/v1/auth/login"
NEW_PASSWORD = "Pass*999"

def _get_token(user):
    string_context = user.get_context_string(FORGOT_PASSWORD)
    return hash_password(string_context)

def test_reset_password(client, user):
    data = {
        "email": user.email,
        "token": _get_token(user),
        "password": NEW_PASSWORD
    }
    response = client.put(f"{base_url}", json=data)
    assert response.status_code == 200
    assert response.json()['message'] == "Your password has been updated."
    del data['token']

    # test login with new password
    login_response = client.post(f"{login_url}", json=data)
    assert login_response.status_code == 200
    assert login_response.json()['message'] == "Login successful"

def test_reset_password_with_invalid_token(client, user):
    data = {
        "email": user.email,
        "token": "somerandomtoken0927430",
        "password": NEW_PASSWORD
    }
    response = client.put(f"{base_url}", json=data)
    assert response.status_code == 400
    del data['token']

    # test login with new password
    login_response = client.post(f"{login_url}", json=data)
    assert login_response.status_code == 400

def test_reset_password_with_invalid_email(client, user):
    data = {
        "email": "random.mail",
        "token": _get_token(user),
        "password": NEW_PASSWORD
    }
    response = client.put(f"{base_url}", json=data)
    assert response.status_code == 422
    del data['token']

    # test login with new password
    login_response = client.post(f"{login_url}", json=data)
    assert login_response.status_code == 422

def test_reset_password_with_wrong_user_email(client, user):
    data = {
        "email": "random@gmail.com",
        "token": _get_token(user),
        "password": NEW_PASSWORD
    }
    response = client.put(f"{base_url}", json=data)
    assert response.status_code == 400
    del data['token']

    # test login with new password
    login_response = client.post(f"{login_url}", json=data)
    assert login_response.status_code == 400

def test_reset_password_with_invalid_password(client, user):
    data = {
        "email": user.email,
        "token": _get_token(user),
        "password": "aaaaaa"
    }
    response = client.put(f"{base_url}", json=data)
    assert response.status_code == 422

def test_reset_password_with_empty_password(client, user):
    data = {
        "email": "random@gmail.com",
        "token": _get_token(user),
        "password": ""
    }
    response = client.put(f"{base_url}", json=data)
    assert response.status_code == 422

def test_reset_password_with_missing_fields(client, user):
    data = {
        "email": "random@gmail.com",
        "password": NEW_PASSWORD
    }
    response = client.put(f"{base_url}", json=data)
    print(response.json())
    assert response.status_code == 422