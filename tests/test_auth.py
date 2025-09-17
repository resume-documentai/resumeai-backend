import uuid

import pytest
from app.core.models.sql_models import UserProfile
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
    
    mock_security_repository.username_exists = MagicMock(return_value=False)
    mock_security_repository.email_exists = MagicMock(return_value=False)
    
    test_data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword"
    }
    
    response = test_client.post("/auth/register", json=test_data)
    
    assert response.json() == {"message": "User registered successfully"}
    assert response.status_code == 200
    
    assert mock_session.add.call_count == add_count + 1
    assert mock_session.commit.call_count == commit_count + 1
    
    user_obj = mock_session.add.call_args[0][0]
    assert user_obj.username == "testuser"
    assert user_obj.email == "testuser@example.com"
    assert verify_password("testpassword", user_obj.password_hash)
    
    assert mock_session.close.call_count == close_count + 1
    
def test_auth_register_user_exists(test_client, mock_security_repository):
    """Test registration with existing email"""
    mock_security_repository.username_exists = MagicMock(return_value=True)
    mock_security_repository.email_exists = MagicMock(return_value=False)
    
    response = test_client.post("/auth/register", json={
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword"
    })
    
    assert response.json() == {"detail": "Username is taken"}
    assert response.status_code == 400
    
    mock_security_repository.username_exists = MagicMock(return_value=False)
    mock_security_repository.email_exists = MagicMock(return_value=True)
    
    response = test_client.post("/auth/register", json={
        "username": "newuser",
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
            "username_or_email": "testuser@example.com",
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
        "username_or_email": "testuser@example.com",
        "password": "wrongpassword"
    })
    
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid password"}
    
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
    user_exists = sr.username_exists("testuser@example.com")
    assert user_exists
    
    mock_session.get_session.return_value.query.return_value.filter.return_value.first.return_value = None
    user_exists = sr.username_exists("testuser@example.com")
    assert not user_exists
    
    mock_session.get_session.return_value.query.return_value.filter.return_value.first.return_value = "User Exists"
    user_exists = sr.email_exists("testuser@example.com")
    assert user_exists
    
    mock_session.get_session.return_value.query.return_value.filter.return_value.first.return_value = None
    user_exists = sr.email_exists("testuser@example.com")
    assert not user_exists


def test_get_user_preferences_success(mock_session, test_client):
    """Test getting user preferences successfully"""
    # Mock the database response
    mock_preferences = {
        "career_goals": "Backend SWE at product-driven companies",
        "industries": ["AI", "DevTools"],
        "target_locations": ["SF", "Seattle", "Remote"],
        "current_status": "Actively applying"
    }
    
    mock_session.query.return_value.filter.return_value.first.return_value = type('obj', (object,), {
        "user_id": "test-user-123",
        "preferences": mock_preferences
    })
    
    # Make the request
    response = test_client.get("/auth/get-preferences?user_id=test-user-123")
    
    # Assert the response
    assert response.status_code == 200
    assert response.json() == {"preferences": mock_preferences}


def test_get_user_preferences_not_found(mock_session, test_client):
    """Test getting preferences for a non-existent user"""
    # Mock no user found
    mock_session.query.return_value.filter.return_value.first.return_value = None
    
    # Make the request
    response = test_client.get("/auth/get-preferences?user_id=non-existent-user")
    
    # Assert the response
    assert response.status_code == 200
    assert response.json() == {"preferences": {}}


def test_set_user_preferences_success(mock_session, test_client):
    """Test setting user preferences successfully"""
    # Mock the database response
    test_user_id = "test-user-123"
    test_preferences = {
        "career_goals": "Backend SWE at product-driven companies",
        "industries": ["AI", "DevTools"],
        "target_locations": ["SF", "Seattle", "Remote"],
        "current_status": "Actively applying"
    }
    
    # Mock the database response for both get and set operations
    mock_session.get_session.return_value.query.return_value.filter.return_value.first.side_effect = [
        None,  # First call (check if exists)
        type('obj', (object,), {'user_id': test_user_id, 'preferences': test_preferences})()  # Second call (return after set)
    ]
    
    # Make the request
    response = test_client.post(
        "/auth/set-preferences",
        json={
            "user_id": test_user_id,
            "preferences": test_preferences
        }
    )
    
    # Assert the response
    assert response.status_code == 200
    assert response.json() == {"message": "User preferences updated successfully"}


def test_set_user_preferences_update_existing(mock_session, test_client):
    """Test updating existing user preferences"""
    test_user_id = "test-user-123"
    existing_preferences = {"career_goals": "old_value",
                            "industries": ["AI", "DevTools"],
                            "target_locations": ["SF", "Seattle", "Remote"],
                            "current_status": "Old Status"}
    new_preferences = {"career_goals": "new_value",
                        "industries": ["AI", "DevTools"],
                        "target_locations": ["SF", "Seattle", "Remote"],
                        "current_status": "New Status"}
    
    # Mock existing user profile
    mock_profile = type('obj', (object,), {
        'user_id': test_user_id,
        'preferences': existing_preferences
    })()
    
    # Mock the database response
    mock_session.get_session.return_value.query.return_value.filter.return_value.first.return_value = mock_profile
    
    # Make the request to update preferences
    response = test_client.post(
        "/auth/set-preferences",
        json={
            "user_id": test_user_id,
            "preferences": new_preferences
        }
    )
    
    # Assert the response
    assert response.status_code == 200
    assert response.json() == {"message": "User preferences updated successfully"}
    
