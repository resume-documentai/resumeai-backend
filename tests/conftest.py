import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.utils.security import create_jwt_token

@pytest.fixture(scope="module")
def test_client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)

@pytest.fixture
async def test_user():
    """Create a test user for authentication tests"""
    return {
        "id": "test_user_id",
        "email": "test@example.com",
        "password": "test_password"
    }

@pytest.fixture
async def test_token(test_user):
    """Create a JWT token for testing"""
    return create_jwt_token(test_user["id"])

@pytest.fixture
async def test_resume():
    """Create a test resume for chat tests"""
    return {
        "id": "test_resume_id",
        "text": "Test resume content",
        "feedback": "Test feedback"
    }
