from typing import Dict
from fastapi import APIRouter, HTTPException, Depends, Form, Query
import heapq
import numpy as np
from app.core.utils.models import Message, ChatSession
from app.core.dependencies import get_database, get_resume_repository, get_file_processing, get_process_llm
from app.services.process_llm import ProcessLLM
from app.services.resume_repository import ResumeRepository
from app.services.file_processing import FileProcessing

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
            resume_data = resume_repository.get_resume_by_file_id(file_id)
            if not resume_data:
                raise HTTPException(status_code=404, detail="Resume not found.")
            
            # Create new chat session
            session = ChatSession(
                messages=[],
                resume=resume_data.get("resume_text", ""),
                feedback=resume_data.get("feedback", "")
            )
            chat_session[file_id] = session
        else:
            session = chat_session[file_id]
        
        resume_text = session.resume
        resume_feedback = session.feedback
        
        formatted_chat_history = "\n".join([f"{msg.type}: {msg.text}" for msg in session.messages])
    
        
        prompt = f"""
            You are a professional recruiter reviewing a resume. Have your feedback be succinct and constructive.
            When asked to give feedback, you should provide a response that uses short bullet points.
            Give some concrete examples of your feedback.
            You can make up some information if you need to, but make sure you let the user know that you are giving an example.
            Ensure your feedback is in raw markdown format, with correct bullet points and formatting.
            If you are unsure about something, you can say that you are unsure.
            Try not to repeat information that has already been given unless explicitly asked to.
            The user has uploaded a resume and received feedback.

            Resume: 
            {resume_text}
            
            Feedback: 
            {resume_feedback}
            
            Chat History:
            {formatted_chat_history}
                        
            User: {message}
            Assistant:
        """
        
        response = process_llm.process(message, model, prompt) or ""
        
        session.messages.append(Message(type="user", text=message))
        session.messages.append(Message(type="bot", text=response))
        
        session_messages_json = [msg.__dict__ for msg in session.messages]

        resume_repository.save_resume_chat_history(file_id, session_messages_json)
        return {"response": response}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
     
@chat_router.get("/start-chat")
async def start_chat(
    file_id: str = Query(None),
    resume_repository: ResumeRepository = Depends(get_resume_repository)):
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
    
@chat_router.get("/similar-resumes")
async def get_similar_resumes(
    user_id: str,
    query: str,
    file_processing: FileProcessing = Depends(get_file_processing),
    resume_repository: ResumeRepository = Depends(get_resume_repository)):
    """
    Get similar resumes for a given user and query.
    
    Args:
        user_id (str): The ID of the user.
        query (str): The query to search for similar resumes.
    
    Returns:
        list: A list of similar resumes.
    """
    try:
        query_embedding = file_processing.generate_embeddings(query)
        
        user_resumes = resume_repository.get_user_resumes(user_id)
        n = len(user_resumes)

        similarties = []
        for doc in user_resumes:
            embedding = np.array(doc["embedding"])
            score = np.dot(query_embedding, embedding) / (np.linalg.norm(query_embedding) * np.linalg.norm(embedding))
            heapq.heappush(similarties, (-score, doc))
    

        return [heapq.heappop(similarties)[1] for _ in range(n)]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))