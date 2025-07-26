from typing import List, Optional
import os
import numpy as np
import heapq

from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Form, Depends

from app.core.dependencies import (
    get_resume_repository,
    get_file_processing,
    get_process_llm,
)
from app.services.file_processing import FileProcessing
from app.services.process_llm import ProcessLLM
from app.services.resume_repository import ResumeRepository
from app.services.llm_prompts import DOCUMENT_TEMPLATE, BASE_PROMPT


resume_router = APIRouter()

# Endpoint to get all resumes for a specific user
@resume_router.get("/", response_model=None)
def get_all_resumes(
    user_id: Optional[str] = Query(None),
    resume_repository: ResumeRepository = Depends(get_resume_repository),
):
    """
    Get all resumes for a specific user.
    
    Args:
        user_id (str): The ID of the user.
    
    Returns:
        list: A list of resumes.
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    try:
        # Print userId for debugging purposes
        # print(user_id)
        resumes_list = resume_repository.get_user_resumes(user_id)

        return resumes_list
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to get a specific resume by user_id and file_id
@resume_router.post("/file", response_model=None)
def get_resume(
    file_id: Optional[str] = Form(...),
    resume_repository: ResumeRepository = Depends(get_resume_repository),
):
    """
    Get a specific resume by user_id and file_id.
    
    Args:
        file_id (str): The ID of the resume file.
    
    Returns:
        dict: A dictionary containing the extracted text and LLM feedback.
    """
    try:
        resume = resume_repository.get_resume(file_id)
        resume_text = resume.resume_text
        resume_feedback = resume.feedback.feedback
        return {"extracted_text": resume_text, "llm_feedback": resume_feedback}
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=404, detail="File not found")

# Endpoint to upload a resume
@resume_router.post("/upload", response_model=None)
async def upload_resume(
    file: UploadFile = File(...),
    model_option: str = Form("openai"),
    user_id : Optional[str] = Form(None),
    resume_repository: ResumeRepository = Depends(get_resume_repository),
    file_processing: FileProcessing = Depends(get_file_processing),
    process_llm: ProcessLLM = Depends(get_process_llm),
):
    """
    Upload a resume and extract information from it.
    
    Args:
        file (UploadFile): The uploaded file.
        model_option (str): The model to use for processing the resume. Defaults to "openai".
        user_id (str, optional): The ID of the user. Defaults to None.
        file_processing (FileProcessing): File processing service.
        process_llm (ProcessLLM): LLM processing service.
        resume_repository (ResumeRepository): Resume repository service.
    
    Returns:
        dict: A dictionary containing the extracted text and LLM feedback.
    """
    try:
        # Write the uploaded file's content to a temporary path
        original_filename = file.filename
        file_ext = file.filename.split(".")[-1]
        temp_path = f"temp.{file_ext}"

        with open(temp_path, "wb") as f:
            file_bytes = await file.read()
            f.write(file_bytes)
        
        #Since file_id is a sha256 hash of the file content, we can use it to check if the file already exists
        file_id = file_processing.generate_file_id(file_bytes)

        # Extract information from file
        txt = file_processing.extract(temp_path, file_ext)    
        os.remove(temp_path)

        if not txt:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        if user_id:
            resume = resume_repository.get_resume(file_id)
            if resume:
                return {"extracted_text": resume.resume_text, "feedback": resume.feedback.feedback}
                    
        document = DOCUMENT_TEMPLATE.format(
            document=txt,
            feedback={},
            chat_history=""
        )

        llm_feedback = process_llm.process(document, model=model_option, prompt=BASE_PROMPT)
        embedding = file_processing.generate_embeddings(txt)
        
        resume_repository.save_resume_feedback(
            user_id=user_id,
            file_id=file_id,
            file_name=original_filename,
            resume_text=txt,
            feedback=llm_feedback,
            embedding=embedding
        )
        
        return {"extracted_text": txt, "feedback": llm_feedback}
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))
    
    
@resume_router.post("/similar-resumes")
async def get_similar_resumes(
    user_id: str = Form(...),
    query: str = Form(...),
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
        query_embedding = np.array(query_embedding)
        
        user_resumes = resume_repository.get_user_resumes(user_id)
        n = len(user_resumes)

        similarities = []
        for doc in user_resumes:
            embedding = np.array(doc.embedding)

            score = np.dot(query_embedding, embedding) / (np.linalg.norm(query_embedding) * np.linalg.norm(embedding))
            heapq.heappush(similarities, (-score, doc))
        results = []
        for score, doc in [heapq.heappop(similarities) for _ in range(n)]:
            results.append({
                "id": doc.id,
                "file_id": doc.file_id,
                "file_name": doc.file_name,
                "created_at": doc.created_at,
                "embedding": doc.embedding,
                "score": -score # negative score because heapq is a min heap
            })
        
        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))