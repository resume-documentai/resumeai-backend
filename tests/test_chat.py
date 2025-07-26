import pytest
from uuid import uuid4
from unittest.mock import MagicMock, patch
from app.core.models.pydantic_models import Message, ChatSession, Feedback, FeedbackCategory
from conftest import mock_resume_repository, test_client, test_resume, test_resume_feedback

@pytest.fixture(scope="function")
def test_chat_session(test_resume, test_resume_feedback):
    return ChatSession(
        messages=[
            Message(type="user", text="Hello"),
            Message(type="bot", text="Hi there!")
        ],
        resume=test_resume.resume_text,
        feedback=test_resume_feedback.feedback,
    )

@pytest.fixture(scope="function")
def test_resume_with_chat(test_resume, test_chat_session):
    test_resume.chat_history = test_chat_session.messages
    test_resume.feedback = test_chat_session.feedback
    test_resume.resume_text = test_chat_session.resume
    return test_resume

def test_start_chat_existing_session(test_client, mock_session, test_resume, test_resume_with_chat):
    """Test starting a chat session with existing chat history"""

    mock_session.query.return_value.join.return_value.join.return_value.filter.return_value.first.return_value = test_resume_with_chat
    
    response = test_client.get(f"/chat/start-chat?file_id={test_resume.file_id}")
    
    # Verify response
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 2  # Should have 2 messages from the chat history
    assert response_data[0]["type"] == "user"
    assert response_data[0]["text"] == "Hello"
    assert response_data[1]["type"] == "bot"
    assert response_data[1]["text"] == "Hi there!"

def test_start_chat_new_session(test_client, mock_session, test_resume, test_resume_with_chat):
    """Test starting a chat session with no existing history"""
    test_resume_with_chat.chat_history = []
    mock_session.query.return_value.join.return_value.join.return_value.filter.return_value.first.return_value = test_resume_with_chat
    
    response = test_client.get(f"/chat/start-chat?file_id={test_resume.file_id}")
    
    assert response.status_code == 200
    assert response.json() == []  # Should return empty list for new session

def test_chat_message(test_client, mock_session, test_resume, test_resume_with_chat, test_resume_feedback):
    """Test sending a chat message with mocked OpenAI response"""
    
    add_count = mock_session.add.call_count
    commit_count = mock_session.commit.call_count
    
    test_resume.feedback = test_resume_feedback.feedback
    test_resume.chatsession = test_resume_with_chat
    
    mock_session.query.return_value.options.return_value.filter.return_value.first.return_value = test_resume

    mock_response = "This is a test response from the AI."
    with patch('app.services.process_llm.ProcessLLM.process') as mock_process:
        mock_process.return_value = {"response": mock_response}
        
        response = test_client.post(
            "/chat/",
            data={
                "file_id": str(test_resume.file_id),
                "message": "Test message",
                "model": "openai"
            }
        )
    # Verify response
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["response"] == mock_response
    
    # Verify session was updated with new messages
    assert mock_session.add.call_count == add_count
    assert mock_session.commit.call_count == commit_count + 1

def test_chat_message_missing_file_id(test_client):
    """Test sending a chat message without file_id"""
    response = test_client.post(
        "/chat/",
        data={
            "message": "Test message",
            "model": "openai"
        }
    )
    
    # Should return 422 for validation error
    assert response.status_code == 422
    assert "field required" in str(response.json()["detail"][0]["msg"]).lower()

def test_chat_message_invalid_file_id(test_client, mock_session):
    """Test sending a chat message with invalid file_id"""
    # Setup mock to return None (resume not found)
    with patch('app.services.resume_repository.ResumeRepository.get_resume') as mock_get_resume:
        mock_get_resume.return_value = None
        invalid_file_id = str(uuid4())
        response = test_client.post(
            "/chat/",
            data={
                "file_id": invalid_file_id,
                "message": "Test message",
                "model": "openai"
            }
        )
    
    # Should return 404 for non-existent resume
    assert response.status_code == 404
    assert "Resume not found" in response.json()["detail"]
