import pytest
from fastapi.testclient import TestClient
from main import app
from app.core.utils.security import create_jwt_token
from unittest.mock import MagicMock

@pytest.fixture(scope="module")
def test_client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)

@pytest.fixture(scope="session")
async def test_user():
    """Create a test user for authentication tests"""
    return {
        "id": "test_user_id",
        "email": "test@example.com",
        "password": "test_password"
    }

@pytest.fixture(scope="session")
async def test_token(test_user):
    """Create a JWT token for testing"""
    return create_jwt_token(test_user["id"])

@pytest.fixture(scope="session")
async def test_resume():
    """Create a test resume for chat tests"""
    return {
        "id": "test_resume_id",
        "text": "Test resume content",
        "feedback": "Test feedback"
    }

@pytest.fixture
def mock_mongodb():
    """Create a mock MongoDB instance for testing"""
    # Create mock collections
    mock_auth_collection = MagicMock()
    mock_resume_collection = MagicMock()
    
    # Create mock database
    mock_db = MagicMock()
    mock_db.get_collection.side_effect = lambda name: {
        "auth_collection": mock_auth_collection,
        "resume_collection": mock_resume_collection
    }.get(name)
    
    # Create mock client
    mock_client = MagicMock()
    mock_client.get_database.return_value = mock_db
    
    # Create mock database instance
    mock_db_instance = MagicMock()
    mock_db_instance.client = mock_client
    mock_db_instance.db = mock_db
    mock_db_instance.users_collection = mock_auth_collection
    mock_db_instance.resume_collection = mock_resume_collection
    
    # Mock the global instance
    from app.core.database import Database
    original_mongodb = Database._instance
    Database._instance = mock_db_instance
    
    # Also mock the global mongodb instance
    Database._instance._client = mock_client
    Database._instance._db = mock_db
    Database._instance._users_collection = mock_auth_collection
    Database._instance._resume_collection = mock_resume_collection
    
    yield mock_db_instance
    
    # Reset the global instance after test
    Database._instance = original_mongodb