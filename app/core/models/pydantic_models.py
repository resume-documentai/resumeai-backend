from typing import List
from datetime import datetime
from pydantic import BaseModel, ConfigDict

def config(cls):
    cls.model_config = ConfigDict()
    return cls

@config
class FeedbackCategory(BaseModel):
    score: float
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]

@config
class Feedback(BaseModel):
    structure_organization: FeedbackCategory
    clarity_conciseness: FeedbackCategory
    grammar_spelling: FeedbackCategory
    impact_accomplishments: FeedbackCategory
    ats_readability: FeedbackCategory
    overall_score: float
    general_feedback: str

# Chat Models
@config
class Message(BaseModel):
    type: str 
    text: str

@config
class ChatSession(BaseModel):   
    messages: List[Message]
    resume: str
    feedback: Feedback

# Auth Models
@config
class UserRegister(BaseModel):
    username: str
    email: str
    password: str

@config
class UserLogin(BaseModel):
    username_or_email: str
    password: str

@config
class SimpleResume(BaseModel):
    id: str
    file_id: str
    file_name: str
    created_at: datetime
    embedding: List[float]