import pytest
from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token

def test_password_hashing_and_verification():
    raw_pwd = "SuperSecretPassword!123"
    hashed = get_password_hash(raw_pwd)
    
    assert hashed != raw_pwd
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_jwt_token_generation_and_decoding():
    payload = {"sub": "engineer1", "role": "technician"}
    token = create_access_token(payload)
    
    assert isinstance(token, str)
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "engineer1"
    assert decoded["role"] == "technician"

def test_login_success(client, test_user):
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "secret123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_password(client, test_user):
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "wrong_password"},
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

def test_login_auto_register_new_user(client):
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "brand_new_user", "password": "password999"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_read_users_me_authenticated(client, auth_headers, test_user):
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == test_user.username
    assert data["role"] == "technician"

def test_read_users_me_unauthenticated(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
