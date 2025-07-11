from typing import List, Optional, Tuple, Any
from threading import Lock

from gridfs import GridFS

from app.core.database import database
from app.core.models.sql_models import (
    Resume,
    ResumeFeedback,
    ResumeEmbedding,
    ChatSession
)
from app.core.models.pydantic_models import Feedback

class ResumeRepository:
    def __init__(self):
        self.db = database
        self._gridfs_instance = None
        self._gridfs_lock = Lock()

    def get_gridfs(self):
        """Get thread-safe GridFS instance"""
        if self._gridfs_instance is None:
            with self._gridfs_lock:
                if self._gridfs_instance is None:
                    self._gridfs_instance = GridFS(self.db._engine)
        return self._gridfs_instance


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
            
            return [{
                "id": str(resume.id),
                "file_id": str(resume.file_id),
                "file_name": resume.file_name,
                "created_at": resume.created_at,
                "embedding": resume.embedding
            } for resume in resumes]
        except Exception as e:
            raise e
        finally:
            session.close()


    def get_resume(self, user_id: str, original_filename: str, resume_text: str):
        """ Get resume by user_id and original_filename """
        session = self.db.get_session()

        try:
            # Get resume by user_id, original_filename, and resume_text
            query = session.query(Resume).filter(
                Resume.user_id == user_id,
                Resume.file_name == original_filename,
                Resume.resume_text == resume_text
            ).first()
            
            return query
        except Exception as e:
            raise e
        finally:
            session.close()

    def save_resume_feedback(self, user_id: str, file_name: str, resume_text: str, feedback: Feedback, file_content: bytes, embedding: List[float]) -> str:
        """ Save resume feedback and return the file_id """
        session = self.db.get_session()
        
        try:
            fs = self.get_gridfs()
            file_id = fs.put(file_content, filename=file_name, content_type="application/pdf")
        
            # Create Query items to be inserted
            resume = Resume(
                user_id=user_id,
                file_id=file_id,
                file_name=file_name,
                resume_text=resume_text,
                general_feedback=feedback.general_feedback,
                overall_score=feedback.overall_score,
            )
            
            feedback = ResumeFeedback(
                id=file_id,
                feedback=feedback.model_dump()
            )
            
            embedding = ResumeEmbedding(
                id=file_id,
                embedding=embedding
            )
            
            chat_session = ChatSession(
                id=file_id,
                chat_history={}
            )
            
            # Add items to session and commit them 
            session.add(resume)
            session.add(feedback)
            session.add(embedding)
            session.add(chat_session)
            session.commit()
        
            return str(file_id)
        except Exception as e:
            # undo changes if an error occurs
            session.rollback()
            raise e
        finally:
            session.close()

    def save_resume_chat_history(self, file_id: str, chat_history: List[dict]):
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

    def get_resume_by_file_id(self, file_id: str) -> Optional[dict]:
        """ Get resume by file_id """
        session = self.db.get_session()
        
        try:
            # Get resume by file_id
            resume = session.query(
                Resume
            ).filter(
                Resume.file_id == file_id
            ).first()
            
            return resume
        except Exception as e:
            raise e
        finally:
            session.close()

    def get_resume_text_and_feedback(self, file_id: str) -> Optional[List[str]]:
        """ Get resume text and feedback by file_id """
        session = self.db.get_session()
        
        try:
            # Get resume by file_id
            resume = session.query(
                Resume
            ).filter(
                Resume.file_id == file_id
            ).first()
            
            return [resume.resume_text, resume.general_feedback]
        except Exception as e:
            raise e
        finally:
            session.close()

    def get_resume_embedding(self, file_id: str) -> Optional[List[float]]:
        """Get resume embedding by file_id"""

        session = self.db.get_session()
        
        try:
            # Get resume by file_id
            resume = session.query(
                ResumeEmbedding
            ).filter(
                ResumeEmbedding.id == file_id
            ).first()
            
            return resume.embedding
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
                Resume.resume_text,
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
            
            return resume.chat_history, resume.resume_text, resume.feedback
        except Exception as e:
            raise e
        finally:
            session.close()