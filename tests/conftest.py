import uuid
from datetime import datetime

import pytest
import numpy as np
from fastapi.testclient import TestClient
from main import app
from unittest.mock import MagicMock

from app.services.security_repository import SecurityRepository
from app.services.resume_repository import ResumeRepository
from app.core.dependencies import get_resume_repository, get_security_repository
from app.core.database import Database
from app.core.models.pydantic_models import FeedbackCategory, Feedback, ChatSession


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


@pytest.fixture(scope="function")
def test_resume():
    resume = MagicMock()
    resume.id = uuid.uuid4()
    resume.user_id = uuid.uuid4()
    resume.file_id = uuid.uuid4()
    resume.file_name = "test_resume.pdf"
    resume.resume_text = "This is a test resume text."
    resume.general_feedback = "This is a test general feedback."
    resume.overall_score = 4.5
    resume.created_at = datetime.now()
    return resume

@pytest.fixture(scope="function")
def test_resume_feedback(test_resume):
    category_data = FeedbackCategory(
        score=4.5,
        strengths=["Strength 1", "Strength 2"],
        weaknesses=["Weakness 1", "Weakness 2"],
        suggestions=["Suggestion 1", "Suggestion 2"]
    )

    feedback_data = Feedback(
        structure_organization= category_data,
        clarity_conciseness= category_data,
        grammar_spelling= category_data,
        impact_accomplishments= category_data,
        ats_readability= category_data,
        overall_score=4.5,
        general_feedback= "This is a test general feedback."
    )
    
    test_data = {
        "id": test_resume.id,
        "feedback": feedback_data,
    }
    
    resume_feedback = MagicMock(**test_data)
    return resume_feedback

@pytest.fixture(scope="function")
def test_resume_chat_history(test_resume):
    chat_history = [
        {"type": "user", "text": "Hello"},
        {"type": "bot", "text": "Hi there!"}
    ]
    
    test_data = {
        "id": test_resume.id,
        "chat_history": chat_history,
    }
    
    resume_chat_history = MagicMock(**test_data)
    return resume_chat_history

@pytest.fixture(scope="function")
def test_resume_embedding(test_resume):
    embedding = np.zeros(1536)
    
    test_data = {
        "id": test_resume.id,
        "embedding": embedding,
    }
    
    resume_embedding = MagicMock(**test_data)
    return resume_embedding
