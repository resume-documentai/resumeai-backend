from app.core.database import Database
from app.services.resume_repository import ResumeRepository
from app.services.process_llm import ProcessLLM
from app.services.file_processing import FileProcessing
from fastapi import Depends
from typing import Any
from functools import lru_cache
from typing import Callable
from unittest.mock import MagicMock

# Global database instance for the application
db_instance = None

# Flag to indicate if we're in test mode
test_mode = False

def set_test_mode(mode: bool):
    """Set test mode for dependencies"""
    global test_mode
    test_mode = mode

def get_mock_database() -> Database:
    """Get a mock database instance for testing"""
    from unittest.mock import MagicMock
    mock_db = Database()
    mock_db._client = MagicMock()
    mock_db._db = MagicMock()
    mock_db._users_collection = MagicMock()
    mock_db._resume_collection = MagicMock()
    return mock_db

@lru_cache()
def get_database() -> Database:
    """Get the database instance"""
    if test_mode:
        return get_mock_database()
    
    if db_instance is None:
        raise RuntimeError("Database not initialized. Call initialize_database() first")
    return db_instance

def get_mock_database() -> Database:
    """Get a mock database instance for testing"""
    mock_db = Database()
    mock_db._client = MagicMock()
    mock_db._db = MagicMock()
    mock_db._users_collection = MagicMock()
    mock_db._resume_collection = MagicMock()
    return mock_db

def get_resume_repository():
    """Get the resume repository instance"""
    db = get_database()
    return ResumeRepository(db)

def get_process_llm() -> ProcessLLM:
    """Get the LLM processing instance"""
    return ProcessLLM()

def get_file_processing() -> FileProcessing:
    """Get the file processing instance"""
    return FileProcessing()

# Override functions for testing
def override_get_database():
    return get_mock_database()

mock_database = get_mock_database
