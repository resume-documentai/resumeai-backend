from app.core.database import Database, database    
from app.services.file_processing import FileProcessing
from app.services.process_llm import ProcessLLM
from app.services.resume_repository import ResumeRepository
from app.services.security_repository import SecurityRepository
from functools import lru_cache


@lru_cache()
def get_database() -> Database:
    """Get the database instance"""
    return database

def get_resume_repository():
    """Get the resume repository instance"""
    db = get_database()
    return ResumeRepository(db)

def get_security_repository():
    """Get the security repository instance"""
    db = get_database()
    return SecurityRepository(db)

def get_process_llm() -> ProcessLLM:
    """Get the LLM processing instance"""
    return ProcessLLM()

def get_file_processing() -> FileProcessing:
    """Get the file processing instance"""
    return FileProcessing()

