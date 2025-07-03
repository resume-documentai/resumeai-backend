from openai import OpenAI
import requests
from app.core.config import LLAMA_SERVER, OPENAI_API_KEY
from typing import Optional

class ProcessLLM:
    def __init__(self):
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
        self.base_prompt = ("You are a professional resume reviewer. "
                           "Analyze the following resume text and provide feedback on the candidate's strengths, weaknesses, "
                           "and suggestions for improvement. Focus on the clarity, relevance, and impact of the information provided. "
                           "Ensure your feedback is in raw markdown format, with correct bullet points and formatting."
                           "Ignore formatting issues and be succinct in your feedback. "
                           "Also, highlight any grammatical errors. Here is the resume text:\n\n")

    def __test_llama_connection(self) -> bool:
        """Test connection to the LLAMA server"""
        try:
            response = requests.get(f"{LLAMA_SERVER}/api/tags", timeout=3)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def __test_openai_connection(self) -> bool:
        """Test connection to the OpenAI API"""
        try:
            response = self.openai_client.models.list()
            return bool(response)
        except Exception:
            return False

    def __process_with_llama(self, extracted_text: str, prompt: str) -> str:
        """Process resume text using the LLAMA server"""
        if not self.__test_llama_connection():
            return "Error: Unable to connect to llama server."

        llama_prompt = f"{prompt}{extracted_text}"

        try:
            response = requests.post(f"{LLAMA_SERVER}/api/generate", json={
                "model": "llama3.1:latest",
                "prompt": llama_prompt
            })
            return response.json().get("response", "No response from llama.")
        except Exception as e:
            return f"Error processing resume: {str(e)}"

    def __process_with_openai(self, extracted_text: str, prompt: str) -> str:
        """Process resume text using the OpenAI API"""
        if not self.__test_openai_connection():
            return "Error: Unable to connect to OpenAI server."

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": extracted_text}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error processing resume: {str(e)}"

    def process(self, extracted_text: str, option: str, prompt: Optional[str] = None) -> str:
        """
        Process resume text using either LLAMA or OpenAI
        Args:
            extracted_text: The resume text to process
            option: 'ollama' or 'openai'
            prompt: Optional custom prompt, uses base_prompt if not provided
        Returns:
            Processed feedback
        """
        prompt = prompt or self.base_prompt
        
        if option == "ollama":
            return self.__process_with_llama(extracted_text, prompt)
        elif option == "openai":
            return self.__process_with_openai(extracted_text, prompt)
        return "Invalid processing option"
    
    
