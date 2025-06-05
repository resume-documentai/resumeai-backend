import pytest
from app.core.utils.security import verify_password, hash_password

@pytest.mark.asyncio
async def test_auth_register(test_client, test_user):
    # Test user registration
    response = test_client.post(
        "/auth/register",
        json={
            "username": test_user["email"].split("@")[0],
            "email": test_user["email"],
            "password": test_user["password"]
        }
    )
    
    assert response.status_code == 200
    assert "token" in response.json()

@pytest.mark.asyncio
async def test_auth_login(test_client, test_user):
    # First register the user
    test_client.post(
        "/auth/register",
        json={
            "username": test_user["email"].split("@")[0],
            "email": test_user["email"],
            "password": test_user["password"]
        }
    )
    
    # Test user login
    login_response = test_client.post(
        "/auth/login",
        json={
            "email": test_user["email"],
            "password": test_user["password"]
        }
    )
    
    assert login_response.status_code == 200
    assert "token" in login_response.json()

@pytest.mark.asyncio
async def test_password_hashing():
    password = "test_password"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False
