import pytest
from bson import ObjectId
from typing import List
from app.core.models.pydantic_models import Message, ChatSession
from unittest.mock import patch

@pytest.mark.asyncio
async def test_start_chat_existing_session(test_client, test_resume_with_chat):
    """Test starting a chat session with existing chat history"""
    # Setup mock database
    mock_resume = test_resume_with_chat
    
    # Mock the resume repository method directly
    with patch('app.services.resume_repository.ResumeRepository.get_resume_by_file_id') as mock_get_resume:
        mock_get_resume.return_value = mock_resume
        
        # Test the endpoint
        response = test_client.get(f"/chat/start-chat?file_id={str(mock_resume['_id'])}")
        assert response.status_code == 200

        # Verify response
        session_data = response.json()
        assert len(session_data) == 2  # Existing chat history
        assert session_data[0]["type"] == "user"
        assert session_data[0]["text"] == "Hello"
        assert session_data[1]["type"] == "bot"
        assert session_data[1]["text"] == "Hi there!"
        
        # Verify that the correct method was called
        mock_get_resume.assert_called_once_with(str(mock_resume['_id']))

@pytest.mark.asyncio
async def test_start_chat_new_session(test_client, test_resume):
    """Test starting a chat session with no existing history"""
    # Setup mock database without chat history
    mock_resume = test_resume
    
    with patch('app.services.resume_repository.ResumeRepository.get_resume_by_file_id') as mock_get_resume:
        mock_get_resume.return_value = mock_resume
    
        # Test the endpoint
        response = test_client.get(f"/chat/start-chat?file_id={str(mock_resume['_id'])}")
        assert response.status_code == 200
        
        # Verify response
        session_data = response.json()
        assert len(session_data) == 0 # No existing chat history


@pytest.mark.asyncio
async def test_chat_message(test_client, mock_mongodb, test_resume_with_chat, test_token):
    """Test sending a chat message with mocked OpenAI response"""
    # Setup mock database
    mock_mongodb.resume_collection.find_one.return_value = test_resume_with_chat
    
    # Mock OpenAI response
    mock_response = "**Feedback:**\n\n- Your resume is GOOD."
    
    # Start a chat session
    start_response = test_client.get(f"/chat/start-chat?file_id={str(test_resume_with_chat['_id'])}")
    assert start_response.status_code == 200
    
    # Send a chat message
    with patch('app.services.process_llm.ProcessLLM.process') as mock_process:
        mock_process.return_value = mock_response
        # Patch save_resume_chat_history to update our test fixture
        with patch('app.services.resume_repository.ResumeRepository.save_resume_chat_history') as mock_save:
            def update_chat_history(file_id: str, chat_history: List[dict]):
                test_resume_with_chat["chat_history"] = chat_history
            mock_save.side_effect = update_chat_history
            message = "What do you think about my resume?"
            chat_response = test_client.post(
                "/chat/",
                data={
                    "file_id": str(test_resume_with_chat['_id']),
                    "message": message,
                    "model": "openai"
                },
                headers={"Authorization": f"Bearer {test_token}"}
            )
            
            assert chat_response.status_code == 200
            response_data = chat_response.json()
            
            # Verify response structure
            assert "response" in response_data
            assert response_data["response"] == mock_response
            
            
            # Verify chat session data
            session = test_resume_with_chat["chat_history"]
            print(session)
            assert len(session) >= 3  # Two original messages + new exchange
            
            # Verify new messages in session
            assert session[-2]["type"] == "user"
            assert session[-2]["text"] == message
            assert session[-1]["type"] == "bot"
            assert session[-1]["text"] == mock_response

@pytest.mark.asyncio
async def test_chat_message_missing_file_id(test_client, test_token):
    """Test sending a chat message without file_id"""
    # Send chat message without file_id
    message = "What do you think about my resume?"
    chat_response = test_client.post(
        "/chat/",
        data={
            "message": message,
            "model": "openai"
        },
        headers={"Authorization": f"Bearer {test_token}"}
    )
    
    assert chat_response.status_code == 422  # Unprocessable entity

@pytest.mark.asyncio
async def test_chat_message_invalid_file_id(test_client, mock_mongodb, test_token):
    """Test sending a chat message with invalid file_id"""
    # Setup mock database to return None
    mock_mongodb.resume_collection.find_one.return_value = None
    invalid_id = ObjectId("000000000000000000000003")
    
    # Send chat message with invalid file_id
    message = "What do you think about my resume?"
    chat_response = test_client.post(
        "/chat/",
        data={
            "file_id": str(invalid_id),
            "message": message,
            "model": "openai"
        },
        headers={"Authorization": f"Bearer {test_token}"}
    )
    
    assert chat_response.status_code == 404  # Internal Server Error
    assert chat_response.json()['detail'] == "Resume not found."