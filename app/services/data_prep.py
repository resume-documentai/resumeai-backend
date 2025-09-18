
import re
from typing import Tuple, List

from app.core.models.pydantic_models import Feedback, FeedbackCategory

class DataPrep:
    def clean_text(text:str) -> str:
        """ Clean text after being extracted from the file """
        lines = text.split("\n")
        cleaned = []
        buffer = ""
        
        bullet_point = re.compile(r"^\s*[\*\+\-\•]\s+")
        sentence_end = re.compile(r"[.:!?…\"\')\]]\s*$")
        possible_headers = re.compile(r"^[A-Z][\w\s,&\-()]{0,40}$")
        print(lines)
        for i, line in enumerate(lines):
            print(line, end=" ")
            
            line = line.strip()
            if not line:
                continue
                
            if bullet_point.match(line):
                print("bullet point")
                if buffer:
                    cleaned.append(buffer.strip())
                buffer = "*" + line[1:]
                continue
                
            if sentence_end.search(line):
                print("sentence end")
                buffer += " " + line
                cleaned.append(buffer.strip())
                buffer = ""
                continue
            
            if possible_headers.match(line):
                print("header")
                if buffer:
                    cleaned.append(buffer.strip())
                cleaned.append(line)
                buffer = ""
                continue
            
            if not buffer:
                print("buffer")
                buffer = line
                continue
            
            buffer += " " + line
            
        if buffer:
            cleaned.append(buffer.strip())
        
        return "\n".join(cleaned)
    
    def extract_skills(text: str) -> List[str]:
        """ Extract skills from the document """

        lines = text.split("\n")
        skills = []

        skill_headers = r"(skills|expertise)"
        stop_headers = r"(experience|education|projects|summary|objective|work history)"

        skill_pattern = re.compile(rf"(.*\b{skill_headers}\b.*)", flags=re.IGNORECASE)
        stop_pattern = re.compile(rf"(.*\b{stop_headers}\b.*)", flags=re.IGNORECASE)
        
        
        in_skills = False

        for i, line in enumerate(lines):
            if in_skills and re.search(stop_pattern, line):
                in_skills = False
                continue
            
            if re.search(skill_pattern, line) and len(line) <= 40:
                in_skills = True
                continue

            if in_skills:
                parts = [part.lstrip() for part in line.split(',')]
                parts = [item for item in parts if item is not '']
                
                skills += parts
                
        return skills
    
    def extract_experiences(text:str) -> List[str]:
        """ Extract experiences from the document """
        pass
    
    def highlight_text(text: str, match: str, color: str) -> str:
        """ Highlight text in the document """
        if match not in text:
            return text
        
        return text.replace(match, "<mark class='" + color + "'>" + match + "</mark>")
    
    def prep_output(text: str, feedback: dict) -> Tuple[str, Feedback]:
        """ Prepare output package to be delivered to frontend """
        categories = ["structure_organization", "clarity_conciseness", "grammar_spelling", "impact_accomplishments", "ats_readability"]
        html_colors = {
            "structure_organization": "bg-green-300", 
            "clarity_conciseness": "bg-yellow-400", 
            "grammar_spelling": "bg-red-300", 
            "impact_accomplishments": "bg-blue-300", 
            "ats_readability": "bg-purple-300"
        }
        formatted_feedback = {}
        overall_score = 0
        try:
            for category in categories:
                suggestions = []
                for suggestion in feedback[category]["suggestions"]:

                    suggestions.append(suggestion["text"])
                    text = DataPrep.highlight_text(
                        text = text,
                        match = suggestion["match"],
                        color = html_colors[category],
                    )
                score = float(feedback[category].get("score"))
                formatted_feedback[category] = FeedbackCategory(
                    score=score,
                    strengths=feedback[category].get("strengths"),
                    weaknesses=feedback[category].get("weaknesses"),
                    suggestions=suggestions
                )

                overall_score += score
            
            formatted_feedback["overall_score"] = round(overall_score / len(categories), 2)
            formatted_feedback["general_feedback"] = feedback.get("general_feedback")
            formatted_feedback = Feedback(**formatted_feedback)

            return text, formatted_feedback
        except Exception as e:
            print("Error preparing output: " + str(e))
            return text, None
            
