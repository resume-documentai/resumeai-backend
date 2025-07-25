import uuid

import pytest
from app.services import security_repository
from conftest import mock_db, mock_security_repository, test_client
from main import app
from unittest.mock import MagicMock, patch

from app.services.security_repository import SecurityRepository
from app.core.utils.security import hash_password, verify_password

   
@pytest.fixture(scope="function")
def test_user():
    user = MagicMock()
    user.user_id = uuid.uuid4()
    user.username = "testuser"
    user.email = "testuser@example.com"
    user.password_hash = hash_password("testpassword")
    return user


def test_auth_register_success(test_client, mock_security_repository, mock_session):
    """Test successful user registration"""
    
    add_count = mock_session.add.call_count
    commit_count = mock_session.commit.call_count
    close_count = mock_session.close.call_count
    
    mock_security_repository.user_exists = MagicMock(return_value=False)
    
    response = test_client.post("/auth/register", json={
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword"
    })
    
    assert response.status_code == 200
    assert response.json() == {"message": "User registered successfully"}
    
    assert mock_session.add.call_count == add_count + 1
    assert mock_session.commit.call_count == commit_count + 1
    
    user_obj = mock_session.add.call_args[0][0]
    assert user_obj.username == "testuser"
    assert user_obj.email == "testuser@example.com"
    assert verify_password("testpassword", user_obj.password_hash)
    
    assert mock_session.close.call_count == close_count + 1
    
def test_auth_register_email_exists(test_client, mock_security_repository):
    """Test registration with existing email"""
    mock_security_repository.user_exists = MagicMock(return_value=True)
    
    response = test_client.post("/auth/register", json={
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword"
    })
    
    assert response.status_code == 400
    assert response.json() == {"detail": "Email already registered"}

def test_auth_login_success(test_client, mock_session, test_user):
    """Test successful login"""
    
    query_count = mock_session.query.call_count
    filter_count = mock_session.query.return_value.filter.call_count
    first_count = mock_session.query.return_value.filter.return_value.first.call_count
    
    mock_session.query.return_value.filter.return_value.first.return_value = test_user
    
    with patch("app.core.utils.security.create_jwt_token", return_value="testtoken"):
        
        response = test_client.post("/auth/login", json={
            "email": "testuser@example.com",
            "password": "testpassword"
        })
    
        assert response.status_code == 200
        assert response.json() == {
            "access_token": "testtoken",
            "user": {
                "user_id": str(test_user.user_id),
                "username": "testuser",
                "email": "testuser@example.com"
            }
        }
        
        assert mock_session.query.call_count == query_count + 1
        assert mock_session.query.return_value.filter.call_count == filter_count + 1
        assert mock_session.query.return_value.filter.return_value.first.call_count == first_count + 1
    
def test_auth_login_invalid_credentials(test_client, mock_session, test_user):
    """Test login with invalid credentials"""
    
    query_count = mock_session.query.call_count
    filter_count = mock_session.query.return_value.filter.call_count
    first_count = mock_session.query.return_value.filter.return_value.first.call_count
    
    mock_session.query.return_value.filter.return_value.first.return_value = test_user
    
    # Test login with invalid password
    response = test_client.post("/auth/login", json={
        "email": "testuser@example.com",
        "password": "wrongpassword"
    })
    
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password"}
    
    assert mock_session.query.call_count == query_count + 1
    assert mock_session.query.return_value.filter.call_count == filter_count + 1
    assert mock_session.query.return_value.filter.return_value.first.call_count == first_count + 1
    
        
def test_auth_root_endpoint(test_client):
    """Test the auth root endpoint"""
    response = test_client.get("/auth/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the authentication service"}
    
def test_password_hashing():
    """Test password hashing functionality"""
    test_password = "testpassword"
    hashed_password = hash_password(test_password)
    assert verify_password(test_password, hashed_password)
    
def test_user_exists(mock_session):
    """Test user exists functionality from security repository"""
    
    sr = SecurityRepository(mock_session)
    
    mock_session.get_session.return_value.query.return_value.filter.return_value.first.return_value = "User Exists"
    user_exists = sr.user_exists("testuser@example.com")
    assert user_exists
    
    mock_session.get_session.return_value.query.return_value.filter.return_value.first.return_value = None
    user_exists = sr.user_exists("testuser@example.com")
    assert not user_exists
    
    
