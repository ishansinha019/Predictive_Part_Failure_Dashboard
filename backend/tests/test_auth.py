import pytest
from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token
from app.models.user import User

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

def test_login_does_not_register_unknown_users(client, db_session):
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "brand_new_user", "password": "password999"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"
    assert db_session.query(User).count() == 0


def test_privileged_usernames_are_not_trusted(client):
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "supervisor", "password": "password999"},
    )
    assert response.status_code == 401


def test_admin_can_create_user_who_can_log_in(client, admin_auth_headers):
    response = client.post(
        "/api/v1/auth/users",
        json={"username": "new.tech", "password": "long-enough-pw", "role": "technician"},
        headers=admin_auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["role"] == "technician"
    assert "hashed_password" not in response.json()

    login = client.post(
        "/api/v1/auth/token",
        data={"username": "new.tech", "password": "long-enough-pw"},
    )
    assert login.status_code == 200


def test_create_user_rejects_duplicates_and_weak_input(client, admin_auth_headers, test_user):
    duplicate = client.post(
        "/api/v1/auth/users",
        json={"username": test_user.username, "password": "long-enough-pw"},
        headers=admin_auth_headers,
    )
    assert duplicate.status_code == 409

    short_password = client.post(
        "/api/v1/auth/users",
        json={"username": "someone", "password": "short"},
        headers=admin_auth_headers,
    )
    assert short_password.status_code == 422

    unknown_role = client.post(
        "/api/v1/auth/users",
        json={"username": "someone", "password": "long-enough-pw", "role": "superuser"},
        headers=admin_auth_headers,
    )
    assert unknown_role.status_code == 422


def test_create_user_requires_admin(client, auth_headers):
    payload = {"username": "sneaky", "password": "long-enough-pw", "role": "admin"}

    assert client.post("/api/v1/auth/users", json=payload).status_code == 401
    assert client.post("/api/v1/auth/users", json=payload, headers=auth_headers).status_code == 403

def test_read_users_me_authenticated(client, auth_headers, test_user):
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == test_user.username
    assert data["role"] == "technician"

def test_read_users_me_unauthenticated(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401

@pytest.mark.parametrize(
    ("method", "path", "json"),
    [
        ("get", "/api/v1/machines/", None),
        ("get", "/api/v1/machines/M-1000/history", None),
        ("get", "/api/v1/parts/P-BRG-02/stats", None),
        ("post", "/api/v1/predictions/predict", {
            "machine_id": "M-1000",
            "part_id": "P-BRG-02",
            "time_in_service_days": 10,
        }),
        ("post", "/api/v1/simulation/daily-scan", None),
    ],
)
def test_data_routes_require_authentication(client, method, path, json):
    response = client.request(method.upper(), path, json=json)
    assert response.status_code == 401
