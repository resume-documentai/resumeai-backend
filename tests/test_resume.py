from tarfile import data_filter
import uuid
from datetime import datetime

import pytest
from conftest import mock_db, mock_security_repository, test_client
from main import app
from unittest.mock import MagicMock, patch
import numpy as np

from app.services.resume_repository import ResumeRepository
from app.core.utils.security import hash_password, verify_password
from app.core.models.pydantic_models import FeedbackCategory, Feedback, ChatSession
from app.services.file_processing import FileProcessing

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

def test_get_all_resumes_success(test_client, mock_session, test_resume):
    """ Test successful retrieval of all resumes through resume root endpoint"""  
    
    query_count = mock_session.query.call_count
    join_count = mock_session.query.return_value.join.call_count
    filter_count = mock_session.query.return_value.join.return_value.filter.call_count
    all_count = mock_session.query.return_value.join.return_value.filter.return_value.all.call_count
    close_count = mock_session.close.call_count
    
    # if there are no resumes
    response = test_client.get("/resumes/?user_id=1")
    
    assert response.status_code == 200
    assert len(response.json()) == 0
    
    assert mock_session.query.call_count == query_count + 1
    assert mock_session.query.return_value.join.call_count == join_count + 1
    assert mock_session.query.return_value.join.return_value.filter.call_count == filter_count + 1
    assert mock_session.query.return_value.join.return_value.filter.return_value.all.call_count == all_count + 1
    assert mock_session.close.call_count == close_count + 1
    
    # if there are two resumes
    mock_session.query.return_value.join.return_value.filter.return_value.all.return_value = [test_resume, test_resume]
    
    response = test_client.get("/resumes/?user_id=1")

    assert response.status_code == 200
    assert len(response.json()) == 2
    
    assert mock_session.query.call_count == query_count + 2
    assert mock_session.query.return_value.join.call_count == join_count + 2
    assert mock_session.query.return_value.join.return_value.filter.call_count == filter_count + 2
    assert mock_session.query.return_value.join.return_value.filter.return_value.all.call_count == all_count + 2
    assert mock_session.close.call_count == close_count + 2
    
def test_get_all_resumes_no_user_id(test_client):
    """ Test retrieval of all resumes through resume root endpoint without user_id"""    
    
    response = test_client.get("/resumes/")
    
    assert response.status_code == 400
    assert response.json() == {"detail": "User ID is required"}
    
def test_get_resume_success(test_client, mock_session, test_resume, test_resume_feedback, test_resume_chat_history, test_resume_embedding):
    """ Test successful retrieval of a specific resume through resume root endpoint"""    
      
    query_count = mock_session.query.call_count
    close_count = mock_session.close.call_count
    
    test_resume.feedback = test_resume_feedback
    test_resume.chatsession = test_resume_chat_history
    test_resume.embedding = test_resume_embedding
    
    mock_session.query.return_value.options.return_value.filter.return_value.first.return_value = test_resume
    
    response = test_client.post("/resumes/file", 
        data={
            "file_id": str(test_resume.file_id)
        })
    
    assert response.status_code == 200
    assert response.json() == {"extracted_text": test_resume.resume_text, "llm_feedback": test_resume.feedback.feedback.model_dump()}
    
    assert mock_session.query.call_count == query_count + 1
    assert mock_session.close.call_count == close_count + 1

def test_get_resume_no_file_id(test_client, mock_session):
    query_count = mock_session.query.call_count
    close_count = mock_session.close.call_count
    
    mock_session.query.return_value.options.return_value.filter.return_value.first.return_value = None
    
    response = test_client.post("/resumes/file",
        data={
            "file_id": "nofileid"
        })
    
    assert response.status_code == 404
    assert response.json() == {"detail": "File not found"}
    
    assert mock_session.query.call_count == query_count + 1
    assert mock_session.close.call_count == close_count + 1
    
@patch("app.services.process_llm.ProcessLLM.process")
@patch("app.services.file_processing.FileProcessing.generate_embeddings")
@patch("app.services.file_processing.FileProcessing.extract")
@patch("app.services.file_processing.FileProcessing.generate_file_id")
def test_upload_resume_success(mock_generate_file_id, mock_extract, mock_generate_embeddings, mock_process, test_client, mock_session, test_resume, test_resume_embedding, test_resume_feedback):
    """ Test successful upload of a resume through upload endpoint"""    
    
    mock_extract.return_value = test_resume.resume_text
    mock_generate_file_id.return_value = test_resume.file_id
    mock_generate_embeddings.return_value = test_resume_embedding.embedding
    mock_process.return_value = test_resume_feedback.feedback
    
    query_count = mock_session.query.call_count
    add_count = mock_session.add.call_count
    commit_count = mock_session.commit.call_count
    close_count = mock_session.close.call_count
    
    file_bytes = bytes(test_resume.resume_text, "utf-8")
    test_filename = "test_resume.pdf"
    
    response = test_client.post("/resumes/upload", 
        files={
            "file": (test_filename, file_bytes, "application/pdf")
        },
        data={
            "model_option": "openai",
            "user_id": str(test_resume.user_id)
        })
    
    assert response.status_code == 200
    assert response.json() == {"extracted_text": test_resume.resume_text, "feedback": test_resume_feedback.feedback.model_dump()}
        
    assert mock_session.query.call_count == query_count + 1
    assert mock_session.add.call_count == add_count + 1
    assert mock_session.commit.call_count == commit_count + 1
    assert mock_session.close.call_count == close_count + 2
    
def test_get_similar_resumes_success(test_client, mock_session, test_resume):
    """ Test successful retrieval of similar resumes through similar resumes endpoint"""    
    test_resume.embedding = np.random.rand(1536)
    mock_session.query.return_value.join.return_value.filter.return_value.all.return_value = [test_resume]
    
    query_count = mock_session.query.call_count
    close_count = mock_session.close.call_count
    
    response = test_client.post("/resumes/similar-resumes", 
        data={
            "user_id": str(test_resume.user_id),
            "query": "test query"
        })
    
    query_embedding = FileProcessing().generate_embeddings("test query")
    expected_score = np.dot(query_embedding, test_resume.embedding) / (np.linalg.norm(query_embedding) * np.linalg.norm(test_resume.embedding))
    
    assert response.status_code == 200
    assert len(response.json()) == 1
    
    assert mock_session.query.call_count == query_count + 1
    assert mock_session.close.call_count == close_count + 1
      
    assert abs(np.float64(response.json()[0]["score"]) - np.float64(expected_score)) < 0.0001

@patch("app.services.file_processing.FileProcessing.extract")
def test_upload_resume_unsupported_file_type(mock_extract, test_client, test_resume):
    """ Test upload with unsupported file type """
    mock_extract.return_value = ""  # Simulate unsupported file type
    
    file_bytes = b"unsupported file content"
    test_filename = "test_resume.xyz"  # Unsupported extension
    
    response = test_client.post("/resumes/upload",
        files={"file": (test_filename, file_bytes, "application/octet-stream")},
        data={"model_option": "openai", "user_id": str(test_resume.user_id)}
    )

    assert response.status_code == 500
    assert "Unsupported file type" in response.json()["detail"]

@patch("app.services.process_llm.ProcessLLM.process")
@patch("app.services.file_processing.FileProcessing.generate_embeddings")
@patch("app.services.file_processing.FileProcessing.extract")
@patch("app.services.file_processing.FileProcessing.generate_file_id")
def test_upload_resume_missing_user_id(mock_generate_file_id, mock_extract, mock_generate_embeddings, mock_process, 
                                     test_client, test_resume, test_resume_embedding, test_resume_feedback):
    """ Test upload when user_id is missing """
    mock_extract.return_value = test_resume.resume_text
    mock_generate_file_id.return_value = test_resume.file_id
    mock_generate_embeddings.return_value = test_resume_embedding.embedding
    mock_process.return_value = test_resume_feedback.feedback
    
    file_bytes = bytes(test_resume.resume_text, "utf-8")
    test_filename = "test_resume.pdf"
    
    # Don't provide user_id in the form data
    response = test_client.post("/resumes/upload",
        files={"file": (test_filename, file_bytes, "application/pdf")},
        data={"model_option": "openai"}
    )
    
    assert response.status_code == 200  # Should still work without user_id
    assert "extracted_text" in response.json()

def test_get_resume_not_found(test_client, mock_session, test_resume):
    """ Test getting a non-existent resume """
    # Setup mock to return None (not found)
    mock_session.query.return_value.options.return_value.filter.return_value.first.return_value = None
    
    response = test_client.post("/resumes/file",
        data={"file_id": "nonexistent_id"}
    )
    
    assert response.status_code == 404
    assert "File not found" in response.json()["detail"]

@patch("app.services.resume_repository.ResumeRepository.get_user_resumes")
def test_get_all_resumes_exception(mock_get_user_resumes, test_client):
    """ Test exception handling in get_all_resumes """
    # Setup mock to raise an exception
    mock_get_user_resumes.side_effect = Exception("Database error")
    
    response = test_client.get("/resumes/?user_id=1")
    
    assert response.status_code == 500
    assert "Database error" in response.json()["detail"]

def test_get_similar_resumes_no_user_id(test_client):
    """ Test getting similar resumes without providing user_id """
    response = test_client.post("/resumes/similar-resumes",
        data={"query": "test query"}
    )
    
    assert response.status_code == 422  # Should be validation error
    assert "field required" in str(response.json()["detail"][0]["msg"]).lower()

@patch("app.services.file_processing.FileProcessing.generate_embeddings")
def test_get_similar_resumes_no_resumes(mock_generate_embeddings, test_client, mock_session):
    """ Test getting similar resumes when user has no resumes """
    # Setup mock to return empty list (no resumes)
    mock_session.query.return_value.join.return_value.filter.return_value.all.return_value = []
    mock_generate_embeddings.return_value = np.random.rand(1536)
    
    response = test_client.post("/resumes/similar-resumes",
        data={
            "user_id": "test_user_id",
            "query": "test query"
        }
    )
    
    assert response.status_code == 200
    assert len(response.json()) == 0
