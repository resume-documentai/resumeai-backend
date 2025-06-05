import pytest
from app.core.utils.models import Message, ChatSession

@pytest.mark.asyncio
async def test_chat_endpoint(test_client, test_resume, test_token):
    # Start a chat session
    start_response = test_client.post(f"/chat/start_chat?file_id={test_resume['id']}")
    assert start_response.status_code == 200
    
    # Test chat endpoint
    message = "What do you think about my resume?"
    chat_response = test_client.post(
        "/chat/",
        data={
            "file_id": test_resume["id"],
            "message": message,
            "model": "openai"
        },
        headers={"Authorization": f"Bearer {test_token}"}
    )
    
    assert chat_response.status_code == 200
    response_data = chat_response.json()
    assert "messages" in response_data
    assert len(response_data["messages"]) == 2  # user message + bot response
    
    # Verify message types
    assert response_data["messages"][0]["type"] == "user"
    assert response_data["messages"][1]["type"] == "bot"

@pytest.mark.asyncio
async def test_start_chat(test_client, test_resume):
    response = test_client.post(f"/chat/start_chat?file_id={test_resume['id']}")
    assert response.status_code == 200
    
    session_data = response.json()
    assert "messages" in session_data
    assert len(session_data["messages"]) == 0
    assert session_data["resume"] == test_resume["text"]
    assert session_data["feedback"] == test_resume["feedback"]
