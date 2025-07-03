from typing import Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Form, Depends
from app.core.dependencies import get_database, get_resume_repository, get_file_processing, get_process_llm
from app.services.file_processing import FileProcessing
from app.services.process_llm import ProcessLLM
from app.services.resume_repository import ResumeRepository
from app.core.database import Database
import os

resume_router = APIRouter()

# Endpoint to get all resumes for a specific user
@resume_router.get("/", response_model=None)
def get_all_resumes(
    resume_repository: ResumeRepository = Depends(get_resume_repository),
    user_id: Optional[str] = Query(None),
):
    """
    Get all resumes for a specific user.
    
    Args:
        user_id (str): The ID of the user.
    
    Returns:
        list: A list of resumes.
    """
    try:
        # Print userId for debugging purposes
        # print(user_id)
        return resume_repository.get_user_resumes(user_id)
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to get a specific resume by user_id and file_id
@resume_router.post("/file", response_model=None)
def get_resume(
    resume_repository: ResumeRepository = Depends(get_resume_repository),
    file_id: Optional[str] = Form(...),
):
    """
    Get a specific resume by user_id and file_id.
    
    Args:
        file_id (str): The ID of the resume file.
    
    Returns:
        dict: A dictionary containing the extracted text and LLM feedback.
    """
    try:
        resume_text, resume_feedback = resume_repository.get_resume_by_file_id(file_id)
        
        return {"extracted_text": resume_text, "llm_feedback": resume_feedback}
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=404, detail="File not found")

# Endpoint to upload a resume
@resume_router.post("/upload", response_model=None)
async def upload_resume(
    resume_repository: ResumeRepository = Depends(get_resume_repository),
    file_processing: FileProcessing = Depends(get_file_processing),
    process_llm: ProcessLLM = Depends(get_process_llm),
    file: UploadFile = File(...),
    modelOption: str = Form("openai"),
    userId: Optional[str] = Form(None),
):
    """
    Upload a resume and extract information from it.
    
    Args:
        file (UploadFile): The uploaded file.
        modelOption (str): The model to use for processing the resume. Defaults to "openai".
        userId (str, optional): The ID of the user. Defaults to None.
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

        # Extract information from file
        txt = await file_processing.extract(temp_path, file_ext)    
        os.remove(temp_path)

        if not txt:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        if userId:
            resume = await resume_repository.get_resume(userId, original_filename, txt)
            if resume:
                return {"extracted_text": resume[0], "llm_feedback": resume[1]}
        
        llm_feedback = await process_llm.process(txt, option=modelOption)
        return {"extracted_text": txt, "llm_feedback": llm_feedback}
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))
    