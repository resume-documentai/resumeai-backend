
import re
from typing import Tuple

from app.core.models.pydantic_models import Feedback, FeedbackCategory

class DataPrep:
    def clean_ocr_text(text:str) -> str:
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
    
    def highlight_text(text: str, match: str) -> str:
        """ Highlight text in the document """
        if match not in text:
            return text
        
        return text.replace(match, "<mark>" + match + "</mark>")
    
    
    def prep_output(text: str, feedback: dict) -> Tuple[str, Feedback]:
        """ Prepare output package to be delivered to frontend """
        categories = ["structure_organization", "clarity_conciseness", "grammar_spelling", "impact_accomplishments", "ats_readability"]
        formatted_feedback = {}
        try:
            for category in categories:
                suggestions = []
                for suggestion in feedback[category]["suggestions"]:

                    suggestions.append(suggestion["text"])
                    text = DataPrep.highlight_text(
                        text = text,
                        match = suggestion["match"],
                    )
                
                formatted_feedback[category] = FeedbackCategory(
                    score=float(feedback[category].get("score")),
                    strengths=feedback[category].get("strengths"),
                    weaknesses=feedback[category].get("weaknesses"),
                    suggestions=suggestions
                )

            formatted_feedback["overall_score"] = float(feedback.get("overall_score"))
            formatted_feedback["general_feedback"] = feedback.get("general_feedback")
            formatted_feedback = Feedback(**formatted_feedback)

            return text, formatted_feedback
        except Exception as e:
            print("Error preparing output: " + str(e))
            return text, None
            
            
            
