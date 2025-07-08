from typing import List, Dict, Any
from pydantic import BaseModel, ConfigDict

def config(cls):
    cls.model_config = ConfigDict()
    return cls

# Chat Models
@config
class Message(BaseModel):
    type: str 
    text: str

@config
class ChatSession(BaseModel):
    messages: List[Message]
    resume: str
    feedback: Dict[str, Any]

# Auth Models
@config
class UserRegister(BaseModel):
    username: str
    email: str
    password: str

@config
class UserLogin(BaseModel):
    email: str
    password: str
