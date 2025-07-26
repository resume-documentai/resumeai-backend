from typing import Dict
from fastapi import APIRouter, HTTPException, Depends, Form, Query
from app.core.models.pydantic_models import ChatSession, Message
from app.core.dependencies import get_resume_repository, get_process_llm
from app.services.process_llm import ProcessLLM
from app.services.resume_repository import ResumeRepository
from app.services.llm_prompts import CHAT_PROMPT, DOCUMENT_TEMPLATE

chat_router = APIRouter()
chat_session: Dict[str, ChatSession] = {}

@chat_router.post("/")
async def chat(
    file_id: str = Form(...), 
    message: str = Form(...), 
    model: str = "openai",
    resume_repository: ResumeRepository = Depends(get_resume_repository),
    process_llm: ProcessLLM = Depends(get_process_llm)
):
    """
    Chat with a resume.
    
    Args:
        file_id (str): The ID of the resume file.
        message (str): The message to send to the chat.
        model (str): The model to use for the chat.
    
    Returns:
        dict: A dictionary containing the response from the chat.
    """
    try:
        if file_id not in chat_session:
            # Try to get resume data from database if not in session
            resume_data = resume_repository.get_resume(file_id)
            if not resume_data:
                raise HTTPException(status_code=404, detail="Resume not found.")

            # Create new chat session
            new_session = ChatSession(
                messages=[],
                resume=resume_data.resume_text,
                feedback=resume_data.feedback.feedback
            )
            chat_session[file_id] = new_session
        else:
            new_session = chat_session[file_id]
        
        resume_text = new_session.resume
        resume_feedback = new_session.feedback
        
        formatted_chat_history = "\n".join([f"{msg.type}: {msg.text}" for msg in new_session.messages])
        formatted_chat_history += f"\nuser: {message}"
    

        document = DOCUMENT_TEMPLATE.format(
            document=resume_text,
            feedback=resume_feedback,
            chat_history=formatted_chat_history,
        )
        llm_response = process_llm.process(text=document, model=model, prompt=CHAT_PROMPT) or ""
        # print("DEBUG", new_session)
        new_session.messages.append(Message(type="user", text=message))
        new_session.messages.append(Message(type="bot", text=llm_response.get("response")))
        session_messages_json = [msg.__dict__ for msg in new_session.messages]

        resume_repository.save_resume_chat_history(file_id, session_messages_json)
        return llm_response
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
     
@chat_router.get("/start-chat")
async def start_chat(
    file_id: str = Query(None),
    resume_repository: ResumeRepository = Depends(get_resume_repository)
):
    """
    Start a chat session for a given resume file. If the chat session already exists, return the existing session.
    
    Args:
        file_id (str): The ID of the resume file.
    
    Returns:
        list: A list of messages in the chat session.
    """
    if file_id in chat_session:
        return [msg.__dict__ for msg in chat_session[file_id].messages]

    messages, txt, feedback = resume_repository.get_resume_chat_messages(file_id)
    session = ChatSession(messages=messages, resume=txt, feedback=feedback)
    chat_session[file_id] = session

    return [msg.__dict__ for msg in session.messages]
    