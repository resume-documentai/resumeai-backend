from pdf2image import convert_from_path
from pytesseract import image_to_string
from docx import Document
import re
from langchain_openai import OpenAIEmbeddings
from typing import Optional, List
import hashlib
import uuid

class FileProcessing:
    def __init__(self):
        self.embedding_model = OpenAIEmbeddings()
        pass
        
    def clean_text(self, text:str) -> str:
        """ Clean text after being extracted from the file """
        lines = text.split("\n")
        cleaned = []
        buffer = ""
        
        garbage_prefix = re.compile(r"^[^\w\s]*([a-z\s\W]{0,20})")
        bullet_point = re.compile(r"^\s*[\*\+\-\•]\s+")
        sentence_end = re.compile(r"[.:!?…\"\')\]]$")
        possible_headers = re.compile(r"^[A-Z][\w\s,&\-()]{0,40}$")
        
        for i, line in enumerate(lines):
            if i == 0 and garbage_prefix.match(line):
                line = line[garbage_prefix.match(line).end():]
            
            line = line.strip()
            if not line:
                if buffer:
                    cleaned.append(buffer.strip())
                    buffer = ""
                continue
                
            if bullet_point.match(line):
                if buffer:
                    cleaned.append(buffer.strip())
                buffer = "*" + line[1:]
                continue
                
            if buffer and sentence_end.match(line):
                cleaned.append(buffer.strip())
                buffer = line
                continue
            
            if possible_headers.match(line):
                if buffer:
                    cleaned.append(buffer.strip())
                cleaned.append(line)
                buffer = ""
                continue
            
            if not buffer:
                buffer = line
                continue
            
            buffer += " " + line
            
        if buffer:
            cleaned.append(buffer.strip())
        
        return "\n".join(cleaned)

    def __from_pdf(self, fp) -> str:
        """Extract text from a PDF file"""
        try:
            images = convert_from_path(fp)
            text = ""
            for image in images:
                text += image_to_string(image)
            text = self.clean_text(text)
            return text
        except Exception as e:
            print("OCR Error: " + str(e))
            return ""

    def __from_docx(self, fp) -> str:
        """Extract text from a DOCX file"""
        try:
            doc = Document(fp)
            return self.clean_text("\n".join([p.text for p in doc.paragraphs]))
        except Exception as e:
            print("Docx Error: " + str(e))
            return ""

    def extract(self, file_path: str, file_ext: str) -> str:
        """
        Extract text from a file based on its extension
        Args:
            file_path: Path to the file
            file_ext: File extension (pdf or docx)
        Returns:
            Extracted text or empty string if unsupported format
        """
        if file_ext == "pdf":
            return self.__from_pdf(file_path)
        elif file_ext == "docx":
            return self.__from_docx(file_path)
        return ""
    
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
