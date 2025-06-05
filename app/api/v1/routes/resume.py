from typing import Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Form
from fastapi.responses import FileResponse
from . import file_processing, resume_repository, process_llm
import os

resume_router = APIRouter()

# Endpoint to get all resumes for a specific user
@resume_router.get("/")
def get_all_resumes(user_id: Optional[str] = Query(None)):
    try:
        # Print userId for debugging purposes
        # print(user_id)
        return resume_repository.get_user_resumes(user_id)
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to get a specific resume by user_id and file_id
@resume_router.post("/file")
def get_resume(file_id: str = Form(...)):

    try:
        resume_text, resume_feedback = resume_repository.get_resume_by_file_id(file_id)
        
        return {"extracted_text": resume_text, "llm_feedback": resume_feedback}
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=404, detail="File not found")

# Endpoint to upload a resume
@resume_router.post("/upload")
async def upload_resume(file: UploadFile = File(...), modelOption: Optional[str] = Form("openai"), userId: Optional[str] = Form(None)):
    # Write the uploaded file's content to a temporary path
    original_filename = file.filename
    file_ext = file.filename.split(".")[-1]
    temp_path = f"temp.{file_ext}"

    with open(temp_path, "wb") as f:
        file_bytes = await file.read()
        f.write(file_bytes)

    # Extract information from file
    txt = file_processing.extract(temp_path, file_ext)    
    os.remove(temp_path)

    # If invalid filetype, raise an error
    if not txt:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # If user is provided, check if a document exists
    if userId:
        resume = resume_repository.get_resume(userId, original_filename, txt)
        if resume:
            return {"extracted_text": resume[0], "llm_feedback": resume[1]}
    
    llm_feedback = process_llm.process(txt, option=modelOption)

    # create embedding and save data
    if userId:
        embedding = file_processing.generate_embeddings(txt)
        resume_repository.save_resume_feedback(userId, original_filename, txt, llm_feedback, file_bytes, embedding)

    return {"extracted_text": txt, "llm_feedback": llm_feedback}