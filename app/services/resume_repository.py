from app.core.database import Database
from pydantic import BaseModel
import gridfs
from bson import ObjectId
import datetime
from typing import List, Optional, Tuple
from threading import Lock

class Resume(BaseModel):
    user_id: str
    file_id: str
    file_name: str 
    resume_text: str
    feedback: str
    embedding: List[float]
    created_at: datetime.datetime

class ResumeRepository:
    def __init__(self, db: Database):
        self.db = db
        self._gridfs_instance = None
        self._gridfs_lock = Lock()

    def get_gridfs(self):
        """Get thread-safe GridFS instance"""
        if self._gridfs_instance is None:
            with self._gridfs_lock:
                if self._gridfs_instance is None:
                    self._gridfs_instance = gridfs.GridFS(self.db.db)
        return self._gridfs_instance


    # Function to get all resumes for a user
    def get_user_resumes(self, user_id: str) -> list[dict]:
        resumes = self.db.resume_collection.find({"user_id": user_id})
        return [{"id": str(resume["_id"]), "file_id": str(resume["file_id"]), "file_name": resume["file_name"], "created_at": resume["created_at"], "embedding": resume["embedding"]} for resume in resumes]

    # Function to get resume by user_id and original_filename
    def get_resume(self, user_id: str, original_filename: str, resume_text: str):
        query = {
            "user_id": user_id,
            "file_name": original_filename,
            "resume_text": resume_text
        }
        result = self.db.resume_collection.find_one(query)
        if result:
            return [result["resume_text"], result["feedback"]]
        return None

    def save_resume_feedback(self, user_id: str, file_name: str, resume_text: str, feedback: str, file_content: bytes, embedding: List[float]) -> str:
        """
        Save resume feedback and return the file_id
        """
        fs = self.get_gridfs()
        file_id = fs.put(file_content, filename=file_name, content_type="application/pdf")
        
        document = {
            "user_id": user_id,
            "file_id": file_id,
            "file_name": file_name,
            "resume_text": resume_text,
            "feedback": feedback,
            "chat_history": [],
            "embedding": embedding,
            "created_at": datetime.datetime.now(tz=datetime.timezone.utc)
        }
        
        self.db.resume_collection.insert_one(document)
        return str(file_id)

    def save_resume_chat_history(self, file_id: str, chat_history: List[dict]):
        """
        Save chat history for a resume
        """
        query = {"_id": ObjectId(file_id)}
        update = {"$set": {"chat_history": chat_history}}
        self.db.resume_collection.update_one(query, update)

    def get_resume_by_file_id(self, file_id: str) -> Optional[dict]:
        """
        Get resume by file_id
        """
        print(file_id)
        return self.db.resume_collection.find_one({"_id": ObjectId(file_id)})

    def get_resume_text_and_feedback(self, file_id: str) -> Optional[List[str]]:
        """
        Get resume text and feedback by file_id
        """
        result = self.get_resume_by_file_id(file_id)
        if result:
            return [result.get("resume_text"), result.get("feedback")]
        return None

    def get_resume_embedding(self, file_id: str) -> Optional[List[float]]:
        """
        Get resume embedding by file_id
        """
        result = self.get_resume_by_file_id(file_id)
        if result:
            return result.get("embedding")
        return None

    def get_resume_chat_messages(self, file_id: str) -> Optional[Tuple[List[dict], str, str]]:
        """
        Get chat history by file_id
        """
        result = self.get_resume_by_file_id(file_id)
        if result:
            return result.get("chat_history"), result.get("resume_text"), result.get("feedback")
        return [None, '', '']