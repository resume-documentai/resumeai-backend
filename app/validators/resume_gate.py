import re

role_keywords = [
    "engineer", "developer", "analyst", "manager", "consultant",
    "scientist", "intern", "architect", "specialist", "administrator",
    "officer", "director", "technician", "designer", "coordinator", "secretary",
    "founder", "cto", "ceo", "researcher", "assistant", "professor"
    ]


# --- Experience Validators ---
def looks_like_job_title(line: str) -> bool:
    """ Check if a line could be a job title """
    return any(re.search(rf"\b{kw}\b", line, re.IGNORECASE) for kw in role_keywords)

def looks_like_exp_bullet(line: str) -> bool:
    """ Check if a line is a bullet point """
    return re.match(r"^[\*\-•]", line.strip()) or re.match(r".*\.$", line.strip())

def looks_like_exp_company(line: str) -> bool:
    """ Check if a line could be a company name """
    if re.search(r"\d", line.strip()) and len(re.findall(r"\d", line.strip())) > 4:
        return False
    
    if re.match(r"^[\*\-•]", line.strip()):
        return False
    return bool(line.strip()) and len(line.strip()) < 40
