import pytest
from fastapi.testclient import TestClient
from main import app
from app.core.utils.security import verify_password, hash_password
from app.core.utils.models import UserRegister, UserLogin
from unittest.mock import patch, MagicMock

@pytest.fixture
def test_client(mock_mongodb):
    """Create a test client with mocked MongoDB"""
    # Create a new client for each test
    return TestClient(app)

test_user = UserRegister(
    email="test@example.com",
    password="test_password",
    username="test_user"
)

def test_auth_register_success(mock_mongodb, test_client):
    """Test successful user registration"""
    # Mock MongoDB operations
    mock_mongodb.users_collection.find_one.return_value = None
    mock_mongodb.users_collection.insert_one.return_value = MagicMock(inserted_id="test_id")
    
    # Mock password hashing to speed up test
    with patch('app.core.utils.security.hash_password', return_value='hashed_password'):
        response = test_client.post(
            "/auth/register/",
            json={
                "username": test_user.username,
                "email": test_user.email,
                "password": test_user.password
            }
        )
    
    assert response.status_code == 200
    assert "message" in response.json()
    assert response.json()["message"] == "User registered successfully"
    
    # Verify MongoDB operations
    mock_mongodb.users_collection.find_one.assert_called_once_with({"email": test_user.email})
    mock_mongodb.users_collection.insert_one.assert_called_once()
    
    # Verify the inserted document
    inserted_doc = mock_mongodb.users_collection.insert_one.call_args[0][0]
    assert inserted_doc["email"] == test_user.email
    assert inserted_doc["username"] == test_user.username
    assert "password" in inserted_doc

def test_auth_register_email_exists(mock_mongodb, test_client):
    """Test registration with existing email"""
    # Mock MongoDB to return existing user
    mock_mongodb.users_collection.find_one.return_value = {
        "email": test_user.email
    }
    
    response = test_client.post(
        "/auth/register/",
        json={
            "username": test_user.username,
            "email": test_user.email,
            "password": test_user.password
        }
    )
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

async def test_auth_login_success(mock_mongodb, test_client):
    """Test successful login"""
    # Mock MongoDB to return user
    mock_mongodb.users_collection.find_one.return_value = {
        "_id": "test_user_id",
        "email": test_user.email,
        "password": hash_password(test_user.password),
        "username": test_user.username
    }
    
    response = test_client.post(
        "/auth/login/",
        json={
            "email": test_user.email,
            "password": test_user.password
        }
    )
    
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "user" in response.json()
    assert response.json()["user"]["user_id"] == "test_user_id"
    assert response.json()["user"]["email"] == test_user.email
    assert response.json()["user"]["username"] == test_user.username
    
    # Verify MongoDB operations
    mock_mongodb.users_collection.find_one.assert_called_once_with({"email": test_user.email})
    
    # Verify the found document
    found_doc = mock_mongodb.users_collection.find_one.return_value
    assert verify_password(test_user.password, found_doc["password"]) is True

def test_auth_login_invalid_credentials(mock_mongodb, test_client):
    """Test login with invalid credentials"""
    # Mock MongoDB to return user with wrong password
    mock_mongodb.users_collection.find_one.return_value = {
        "_id": "test_user_id",
        "email": test_user.email,
        "password": hash_password("wrong_password"),
        "username": test_user.username
    }
    
    response = test_client.post(
        "/auth/login/",
        json={
            "email": test_user.email,
            "password": test_user.password
        }
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"

def test_auth_login_user_not_found(mock_mongodb, test_client):
    """Test login when user doesn't exist"""
    # Mock MongoDB to return None
    mock_mongodb.users_collection.find_one.return_value = None
    
    response = test_client.post(
        "/auth/login/",
        json={
            "email": test_user.email,
            "password": test_user.password
        }
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"

def test_password_hashing():
    """Test password hashing functionality"""
    password = "test_password"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False

def test_auth_root_endpoint(test_client):
    """Test the auth root endpoint"""
    response = test_client.get("/auth/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the authentication service"}