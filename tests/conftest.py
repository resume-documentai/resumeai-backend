import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import MagicMock

from app.services.security_repository import SecurityRepository
from app.services.resume_repository import ResumeRepository
from app.core.dependencies import get_resume_repository, get_security_repository
from app.core.database import Database


@pytest.fixture(scope="module")
def mock_session():
    session = MagicMock()
    return session

@pytest.fixture(scope="module")
def mock_db(mock_session):
    """ Mock resume repository for an empty database """
    mock_db = MagicMock(spec=Database)
    mock_db.get_session.return_value = mock_session
    return mock_db

@pytest.fixture(scope="module")
def mock_resume_repository(mock_db):
    """ Mock resume repository for an empty database """
    mock_resume_repository = ResumeRepository(mock_db)
    return mock_resume_repository

@pytest.fixture(scope="module")
def mock_security_repository(mock_db):
    """ Mock security repository for an empty database """
    mock_security_repository= SecurityRepository(mock_db)
    return mock_security_repository

@pytest.fixture(scope="module")
def test_client(mock_resume_repository, mock_security_repository):
    """Create a test client for the FastAPI app"""  
    app.dependency_overrides[get_resume_repository] = lambda: mock_resume_repository
    app.dependency_overrides[get_security_repository] = lambda: mock_security_repository
    
    yield TestClient(app)
    
    app.dependency_overrides.clear()

