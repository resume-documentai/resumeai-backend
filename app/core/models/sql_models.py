from sqlalchemy import Column, String, DateTime, text, Text, Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from pgvector.sqlalchemy import Vector
from uuid import UUID
import uuid
import os

Base = declarative_base()
DATABASE_URL = os.getenv("DATABASE_URL")

class AuthUser(Base):
    __tablename__ = 'auth_users'
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))

class Resume(Base):
    __tablename__ = 'resumes'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('auth_users.user_id'), nullable=False)
    file_id = Column(UUID(as_uuid=True), nullable=False)
    file_name = Column(Text, nullable=False)
    resume_text = Column(Text)
    general_feedback = Column(Text)
    overall_score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    
class ResumeFeedback(Base):
    __tablename__ = 'resume_feedback'
    
    id = Column(UUID(as_uuid=True), ForeignKey('resumes.id'), primary_key=True, ondelete='CASCADE')
    feedback = Column(JSONB)

class ChatSession(Base):
    __tablename__ = 'chat_sessions'
    
    id = Column(UUID(as_uuid=True), ForeignKey('resumes.id'), primary_key=True, ondelete='CASCADE')
    chat_history = Column(JSONB)
    
class ResumeEmbedding(Base):
    __tablename__ = 'resume_embeddings'
    
    id = Column(UUID(as_uuid=True), ForeignKey('resumes.id'), primary_key=True, ondelete='CASCADE')
    embedding = Column(Vector(1536))
