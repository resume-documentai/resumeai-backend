from typing import List, Optional, Tuple, Any
import hashlib

from sqlalchemy.orm import joinedload

from app.core.database import Database
from app.core.models.sql_models import (
    Resume,
    ResumeFeedback,
    ResumeEmbedding,
    ChatSession
)
from app.core.models.pydantic_models import Feedback, SimpleResume

class ResumeRepository:
    def __init__(self, db: Database):
        self.db = db

    def get_user_resumes(self, user_id: str):
        """Get all resumes for a user"""
        session = self.db.get_session()
        try:
            
            # Get all resumes for a user from resume table and join with embedding table to get embedding
            resumes = session.query(
                Resume.id,
                Resume.file_id,
                Resume.file_name,
                Resume.created_at,
                ResumeEmbedding.embedding
            ).join(
                ResumeEmbedding,
                ResumeEmbedding.id == Resume.id
            ).filter(
                Resume.user_id == user_id
            ).all()
            
            return [
                SimpleResume(
                    id=str(resume.id),
                    file_id=str(resume.file_id),
                    file_name=resume.file_name,
                    created_at=resume.created_at,
                    embedding=resume.embedding
                ) for resume in resumes
            ]
        except Exception as e:
            raise e
        finally:
            session.close()


    def get_resume(self,
        file_id: str
    ) -> Optional[Resume]:
        """ Get resume by file_id """
        session = self.db.get_session()

        try:
            # Get resume by file_id
            query = session.query(Resume).options(
                joinedload(Resume.feedback),
                joinedload(Resume.chatsession),
                joinedload(Resume.embedding)
            ).filter(
                Resume.file_id == file_id
            ).first()
            
            return query
        except Exception as e:
            raise e
        finally:
            session.close()

    def save_resume_feedback(self,
        user_id: str,
        file_id: str,
        file_name: str,
        raw_text: str,
        highlighted_text: str,
        feedback: Feedback,
        embedding: List[float]
    ) -> str:
        """ Save resume feedback and return the file_id """
        session = self.db.get_session()
        try:
            # Create Query items to be inserted
            feedback_obj = ResumeFeedback(
                id=file_id,
                feedback=feedback.model_dump()
            )
            
            embedding_obj = ResumeEmbedding(
                id=file_id,
                embedding=embedding
            )
            chat_session_obj = ChatSession(
                id=file_id,
                chat_history={}
            )
            
            resume = Resume(
                user_id=user_id,
                file_id=file_id,
                file_name=file_name,
                raw_text=raw_text,
                highlighted_text=highlighted_text,
                general_feedback=feedback.general_feedback,
                overall_score=feedback.overall_score,
                feedback=feedback_obj,
                chatsession=chat_session_obj,
                embedding=embedding_obj,
            )
            
            # Add resume and commit since it is required for the other tables
            session.add(resume)
            session.commit()

            return str(file_id)
        except Exception as e:
            # undo changes if an error occurs
            print(e)
            session.rollback()
            raise e
        finally:
            session.close()

    def save_resume_chat_history(self,
        file_id: str,
        chat_history: List[dict]
    ):
        """ Save chat history for a resume """
        session = self.db.get_session()
        
        try:
            resume = session.query(
                Resume.id
            ).filter(
                Resume.file_id == file_id
            ).first()
            
            if not resume:
                raise ValueError(f"No resume found with file_id {file_id}")
            
            # Get chat session by file_id
            chat_session = session.query(
                ChatSession
            ).filter(
                ChatSession.id == resume.id 
            ).first()
            
            # Update chat history
            chat_session.chat_history = chat_history
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_resume_embedding(self, file_id: str) -> Optional[List[float]]:
        """Get resume embedding by file_id"""

        session = self.db.get_session()
        
        try:
            # Get resume by file_id
            resume = session.query(Resume).options(
                joinedload(Resume.embedding)
            ).filter(
                Resume.file_id == file_id
            ).first()
            
            return resume.embedding.embedding
        except Exception as e:
            raise e
        finally:
            session.close()

    def get_resume_chat_messages(self, file_id: str) -> Optional[Tuple[List[dict], str, List[Any]]]:
        """ Get chat history by file_id """
        session = self.db.get_session()
        
        try:
            # Get resume by file_id
            resume = session.query(
                ChatSession.chat_history,
                Resume.raw_text,
                ResumeFeedback.feedback
            ).join(
                Resume,
                Resume.id == ChatSession.id
            ).join(
                ResumeFeedback,
                ResumeFeedback.id == Resume.id
            ).filter(
                Resume.file_id == file_id
            ).first()
            
            return list(resume.chat_history), resume.raw_text, resume.feedback
        except Exception as e:
            raise e
        finally:
            session.close()