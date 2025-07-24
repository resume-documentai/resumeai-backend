from openai import OpenAI
import requests
from app.core.config import LLAMA_SERVER, OPENAI_API_KEY
from typing import Dict
from app.core.models.pydantic_models import Feedback
from app.services.llm_prompts import BASE_PROMPT
import json

class ProcessLLM:
    def __init__(self):
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
        self.base_prompt = BASE_PROMPT
        
        self.temperature = 0.0
        self.max_tokens = 2000

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

    def __process_with_llama(self, text: str, prompt: str) -> Dict:
        """Process resume text using the LLAMA server"""
        if not self.__test_llama_connection():
            return {"error": "Unable to connect to llama server."} 

        try:
            response = requests.post(f"{LLAMA_SERVER}/api/generate", json={
                "model": "llama3.1:latest",
                "prompt": text,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
        
            })
            return response.json().get("response", "No response from llama.")
        
        except json.JSONDecodeError:
            return {"error": f"Failed to parse JSON response: {str(e)}"}
        except Exception as e:
            return {"error": f"Error processing resume: {str(e)}"}

    def __process_with_openai(self, text: str, prompt: str) -> Feedback:
        """Process resume text using the OpenAI API"""
        if not self.__test_openai_connection():
            return {"error": "Unable to connect to OpenAI server."}

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            try:
                json_response = json.loads(response.choices[0].message.content)
                # print(json.dumps(json_response, indent=2))
                feedback = Feedback(**json_response)
                return feedback
            except json.JSONDecodeError as e:
                return {"error": f"Failed to parse JSON response: {str(e)}"}
        except Exception as e:
            return {"error": f"Error processing resume: {str(e)}"}

    def process(self, text: str, model: str, prompt: str) -> dict:
        """
        Process resume text using either LLAMA or OpenAI
        Args:
            text: The resume text to process - already formatted with document template
            model: 'ollama' or 'openai'
            prompt: custom prompt
        Returns:
            Processed feedback
        """
        if model == "ollama":
            return self.__process_with_llama(text, prompt)
        elif model == "openai":
            return self.__process_with_openai(text, prompt)
        return {"error": "Invalid processing option"}
    
    
