import pdfminer.high_level
from docx import Document
import numpy as np
from langchain_openai import OpenAIEmbeddings
from typing import Optional, List
import hashlib
import uuid

class FileProcessing:
    def __init__(self):
        self.embedding_model = OpenAIEmbeddings()

    def __from_pdf(self, fp) -> str:
        """Extract text from a PDF file"""
        return pdfminer.high_level.extract_text(fp)

    def __from_docx(self, fp) -> str:
        """Extract text from a DOCX file"""
        doc = Document(fp)
        return "\n".join([p.text for p in doc.paragraphs])

    def extract(self, file_path: str, file_ext: str) -> Optional[str]:
        """
        Extract text from a file based on its extension
        Args:
            file_path: Path to the file
            file_ext: File extension (pdf or docx)
        Returns:
            Extracted text or None if unsupported format
        """
        if file_ext == "pdf":
            return self.__from_pdf(file_path)
        elif file_ext == "docx":
            return self.__from_docx(file_path)
        return None
    
    def generate_file_id(self, file_content: bytes) -> uuid.UUID:
        """Generate a unique file ID based on file content using SHA-256"""
        sha256 = hashlib.sha256(file_content).hexdigest()
        file_uuid = uuid.UUID(bytes=bytes.fromhex(sha256)[:16])
        return file_uuid

    def generate_embeddings(self, text: str) -> List[List[float]]:
        """
        Generate embeddings for the given text using OpenAI
        Args:
            text: Text to generate embeddings for
        Returns:
            List of embeddings
        """
        return self.embedding_model.embed_documents([text])[0]

