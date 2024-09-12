from tests.conftest import USER_FIRSTNAME, USER_LASTNAME, USER_PASSWORD

base_url = "/api/v1/auth/register"

def test_create_user(client):
    data = {
        "email": "random@gmail.com",
        "password": USER_PASSWORD,
        "last_name": USER_LASTNAME,
        "first_name": USER_FIRSTNAME
    }
    response = client.post(f"{base_url}", json=data)
    assert response.status_code == 201
    assert response.json()['message'] == f"User {data['email']} created successfully"
    assert "password" not in response.json()['data']

def test_create_with_existing_email(client, inactive_user):
    data = {
        "email": inactive_user.email,
        "password": USER_PASSWORD,
        "last_name": USER_LASTNAME,
        "first_name": USER_FIRSTNAME
    }
    response = client.post(f"{base_url}", json=data)
    assert response.status_code == 400

def test_create_with_missing_fields(client):
    data = {
        "email": "random@gmail.com",
        "last_name": USER_LASTNAME,
        "first_name": USER_FIRSTNAME
    }
    response = client.post(f"{base_url}", json=data)
    print(response.json())
    assert response.status_code == 422

def test_create_with_invalid_email(client):
    data = {
        "email": "randommail.com",
        "password": USER_PASSWORD,
        "last_name": USER_LASTNAME,
        "first_name": USER_FIRSTNAME
    }
    response = client.post(f"{base_url}", json=data)
    assert response.status_code == 422

def test_create_with_char_password(client):
    data = {
        "email": "random@mail.com",
        "password": "aaaaaaaaa",
        "last_name": USER_LASTNAME,
        "first_name": USER_FIRSTNAME
    }
    response = client.post(f"{base_url}", json=data)
    assert response.status_code == 422

def test_create_with_numeric_password(client):
    data = {
        "email": "random@mail.com",
        "password": "888888888888888888",
        "last_name": USER_LASTNAME,
        "first_name": USER_FIRSTNAME
    }
    response = client.post(f"{base_url}", json=data)
    assert response.status_code == 422

def test_create_with_alphanumeric_password(client):
    data = {
        "email": "random@mail.com",
        "password": "adkak9087983nmke789",
        "last_name": USER_LASTNAME,
        "first_name": USER_FIRSTNAME
    }
    response = client.post(f"{base_url}", json=data)
    assert response.status_code == 422