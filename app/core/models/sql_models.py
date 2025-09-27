import os
import uuid
from sqlalchemy import Column, String, DateTime, text, Text, Float, ForeignKey, UUID
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
# from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship, declarative_base
from pgvector.sqlalchemy import Vector


Base = declarative_base()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./resumeai.db")


# --- Auth Model ---
class AuthUser(Base):
    __tablename__ = 'auth_users'
    
    user_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    
    experience_embeddings = relationship("ResumeExperienceEmbeddings", 
                                       back_populates="user",
                                       cascade="all, delete-orphan")

# --- User Profile Model ---
class UserProfile(Base):
    __tablename__ = 'user_profiles'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('auth_users.user_id'), primary_key=True)
    skills = Column(JSONB, nullable=True)
    preferences = Column(JSONB, nullable=True)

# --- Resume Models ---
class Resume(Base):
    __tablename__ = 'resumes'
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('auth_users.user_id'), nullable=False)
    file_id = Column(UUID(as_uuid=True), nullable=False)
    file_name = Column(Text, nullable=False)
    raw_text = Column(Text)
    highlighted_text = Column(Text)
    general_feedback = Column(Text)
    overall_score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    
    feedback = relationship("ResumeFeedback",
                            back_populates="resume",
                            uselist=False,
                            cascade="all, delete-orphan",
                            single_parent=True)
    chatsession = relationship("ChatSession",
                            back_populates="resume",
                            uselist=False,
                            cascade="all, delete-orphan",
                            single_parent=True)
    embedding = relationship("ResumeEmbedding",
                            back_populates="resume",
                            uselist=False,
                            cascade="all, delete-orphan",
                            single_parent=True)
    
class ResumeFeedback(Base):
    __tablename__ = 'resume_feedback'
    
    id = Column(UUID, ForeignKey('resumes.id', ondelete='CASCADE'), primary_key=True)
    feedback = Column(JSONB)

    resume = relationship("Resume",
                            back_populates="feedback",
                            uselist=False,
                            cascade="all, delete-orphan",
                            single_parent=True)

class ChatSession(Base):
    __tablename__ = 'chat_sessions'
    
    id = Column(UUID, ForeignKey('resumes.id', ondelete='CASCADE'), primary_key=True)
    chat_history = Column(JSONB)
    
    resume = relationship("Resume",
                            back_populates="chatsession",
                            uselist=False,
                            cascade="all, delete-orphan",
                            single_parent=True)
    
# --- Resume Embedding Models ---
class ResumeEmbedding(Base):
    __tablename__ = 'resume_embeddings'
    
    id = Column(UUID, ForeignKey('resumes.id', ondelete='CASCADE'), primary_key=True)
    embedding = Column(Vector(1536))

    resume = relationship("Resume",
                            back_populates="embedding",
                            uselist=False,
                            cascade="all, delete-orphan",
                            single_parent=True)

class ResumeExperienceEmbeddings(Base):
    """ 
    Resume Experience Embeddings 
        user_id: a user can have multiple experience embeddings
        experience_id: id for experience in resume
        experience_json: experience as parsed by resume
        embedding: vector embedding of experience
    """
    __tablename__ = 'resume_experience_embeddings'
    
    experience_id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey('auth_users.user_id', ondelete='CASCADE'))
    experience_json = Column(JSONB)
    embedding = Column(Vector(1536))

    user = relationship("AuthUser",
                            back_populates="experience_embeddings",
                            uselist=False,
                            cascade="all, delete-orphan",
                            single_parent=True)


# engine = create_engine(DATABASE_URL)
# Base.metadata.create_all(bind=engine)

# print("Tables created successfully.")