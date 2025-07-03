import pytest
from fastapi.testclient import TestClient
from main import app
from app.core.utils.security import create_jwt_token
from app.core.dependencies import db_instance, get_mock_database, set_test_mode
from bson import ObjectId

@pytest.fixture(scope="module")
def test_client():
    """Create a test client for the FastAPI app"""  
    set_test_mode(True)
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
        "_id": ObjectId("000000000000000000000001"),
        "resume_text": "Test resume content",
        "feedback": "Test feedback",
        "chat_history": []
    }
    
@pytest.fixture(scope="session")
def test_resume_with_chat():
    """Create a test chat history for chat tests"""
    return {    
        "_id": ObjectId("000000000000000000000002"),
        "resume_text": "Test resume content",
        "feedback": "Test feedback",
        "chat_history": [
            {"type": "user", "text": "Hello"},
            {"type": "bot", "text": "Hi there!"}
        ]
    }


@pytest.fixture(scope="function")
def mock_mongodb():
    """Create a mock database for testing"""
    from app.core.dependencies import db_instance, get_mock_database
    
    # Save original database instance
    original_db = db_instance
    
    # Set test mode
    original_mode = set_test_mode(True)
    
    # Create mock database
    mock_db = get_mock_database()
    mock_db.users_collection.find_one.return_value = test_user
    mock_db.resume_collection.find_one.return_value = test_resume_with_chat
    
    yield mock_db
    
    # Reset test mode
    set_test_mode(original_mode)
    # Restore original database instance after tests
    db_instance = original_db
