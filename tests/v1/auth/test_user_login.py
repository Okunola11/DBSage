"""
1. Registered users should be able to login
2. Incorrect password should not be accepted
3. Inactive and unverified users should not be able to login
"""

from tests.conftest import USER_PASSWORD

base_url = "/api/v1/auth/login"

def test_user_login(client, user):
    data = {"email": user.email, "password": USER_PASSWORD}
    response = client.post(f"{base_url}", json=data)
    assert response.status_code == 200
    assert response.json()['message'] == "Login successful"
    assert response.json()['access_token'] is not None

def test_user_login_with_wrong_password(client, user):
    response = client.post(f"{base_url}", json={"email": user.email, "password": "randompassword"})
    assert response.status_code == 400
    assert response.json()['message'] == "Incorrect email or password"

def test_user_login_with_wrong_email(client):
    response = client.post(f"{base_url}", json={"email": "random@mail.com", "password": "randompassword"})
    assert response.status_code == 400
    assert response.json()['message'] == "Invalid request!"

def test_user_login_with_inactive_account(client, inactive_user):
    response = client.post(f"{base_url}", json={"email": inactive_user.email, "password": USER_PASSWORD})
    assert response.status_code == 400
    assert response.json()['message'] == "Your account has been deactivated. Please contact support."

def test_user_login_with_unverified_account(client, unverified_user):
    response = client.post(f"{base_url}", json={"email": unverified_user.email, "password": USER_PASSWORD})
    assert response.status_code == 400
    assert response.json()['message'] == "Your account is not verified. Please check your email inbox to verify your account."
