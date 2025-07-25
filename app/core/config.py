from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # MongoDB configuration
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://${MONGODB_USER}:${MONGODB_PASSWORD}@mongodb:27017/resumeai?authSource=admin")
    
    # JWT configuration
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-default-secret-key")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60 * 24  # 24 hours
    
    # LLM configuration
    LLAMA_SERVER: str = os.getenv("LLAMA_SERVER", "http://localhost:11434")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Application configuration
    APP_NAME: str = "ResumeAI Backend"
    API_V1_STR: str = "/api/v1"
    
    class Config:
        case_sensitive = True

# Create instance of settings
settings = Settings()

# Export commonly used settings
JWT_SECRET = settings.JWT_SECRET
JWT_ALGORITHM = settings.JWT_ALGORITHM
JWT_EXPIRATION_MINUTES = settings.JWT_EXPIRATION_MINUTES
MONGO_URI = settings.MONGO_URI
LLAMA_SERVER = settings.LLAMA_SERVER
OPENAI_API_KEY = settings.OPENAI_API_KEY
