"""
- Users should be able to send forgot password request
- Forgot password from unregistered emails should just return the success message with nothing done for security
- Unverified users should not be able to request forgot password email
- Inactive users should not be able to request forgot password email 
"""

from app.core.config.email import fm

base_url = "/api/v1/auth/forgot-password"

def test_user_can_send_forgot_password_request(client, user):
    # fm.config.SUPPRESS_SEND = 0
    data = {"email": user.email}
    response = client.post(f"{base_url}", json=data)
    assert response.status_code == 200

def test_no_mail_is_sent_for_unregistered_email(client):
    fm.config.SUPPRESS_SEND = 0
    data = {"email": "parle@gmail.com"}
    response = client.post(f"{base_url}", json=data)
    assert response.status_code == 200

def test_user_cannot_send_forgot_password_request_with_invalid_email(client):
    data = {"email": "invalid.email"}
    response = client.post(f"{base_url}", json=data)
    assert response.status_code == 422

def test_unverified_user_cannot_send_forgot_password_request(client, unverified_user):
    data = {"email": unverified_user.email}
    response = client.post(f"{base_url}", json=data)
    assert response.status_code == 400

def test_inactive_user_cannot_send_forgot_password_request(client, inactive_user):
    data = {"email": inactive_user.email}
    response = client.post(f"{base_url}", json=data)
    assert response.status_code == 400