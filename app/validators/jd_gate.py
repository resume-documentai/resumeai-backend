import re
from collections import Counter

POS_HEADERS = re.compile(
    r"\b(Responsibilities|Duties|What (you'?ll|you will) do|Qualifications|Requirements|Preferred|Nice to have|Benefits|Compensation|About the role|About us)\b",
    re.I,
)

LEGAL = re.compile(r"\b(EEO|equal opportunity|accommodation|background check|drug[- ]?screen)\b", re.I)
APPLY = re.compile(r"\b(apply|submit (your )?application|requisition|job id)\b", re.I)
SALARY = re.compile(r"\$\s?\d{2,3}(,\d{3})?(\s?-\s?\$\s?\d{2,3}(,\d{3})?)?\s?(k|per\s?(year|hour)|/year|/hr|yr|hour)\b", re.I)
LOCATION = re.compile(r"\b[A-Z][a-zA-Z]+,\s?[A-Z]{2}\b")
YEARS = re.compile(r"\b\d{1,2}\+?\s?(years|yrs)\b", re.I)


def bullet_stats(text: str):
    """ Get stats about bullets
    Args:
        text (str): The text to analyze
    
    Returns:
        tuple: A tuple containing the number of bullet points and the average length of the bullet points
    """
    
    bullet_points = re.findall(r"(?m)^\s*[-•*]\s+.+$", text)
    avg_len = 0
    
    if bullet_points:
        lens = [len(bullet) for bullet in bullet_points]
        avg_len = sum(lens) / max(1, len(lens))
        
    return len(bullet_points), avg_len

def pronoun_counts(text: str):
    """ Count the number of pronouns in the text 
    Args:
        text (str): The text to analyze
    Returns:
        tuple: A tuple containing the number of first, second and third person pronouns
    """
    words = re.findall(r"[A-Za-z]+", text.lower())
    c = Counter(words)
    
    first = c["i"] + c["me"] + c["my"] + c["mine"]
    second = c["you"] + c["your"] + c["yours"]
    third = c["we"] + c["us"] + c["our"] + c["ours"] + c["they"] + c["them"] + c["theirs"]
    
    return first, second, third

def jd_score(text: str):
    """ Calculate the validity of the job description 
    Args:
        text (str): The text to analyze
    Returns:
        float: The validity of the job description
    """
    
    length = len(text)
    score = 0
    reasons = []
    
    # Length checks
    if length < 500:
        reasons.append("Too short (< 500 characters)")
        return 10, reasons 
    
    if length > 15000:
        reasons.append("Too long (> 15,000 characters). Consider trimming the boilerplate.")
        score -= 5       
        
    # Postive Signals
    pos_hits = sum(bool(p.search(text)) for p in [POS_HEADERS, LEGAL, APPLY, SALARY, LOCATION, YEARS])
    score += pos_hits * 10
    
    if POS_HEADERS.search(text):
        reasons.append("Has Job Description Headers")
    if LEGAL.search(text):
        reasons.append("Has Hiring/Legal Boilerplate")
    if APPLY.search(text):
        reasons.append("Has Application/Requisition Language.")
    if SALARY.search(text):
        reasons.append("Has Salary/Compensation Information")
    if LOCATION.search(text):
        reasons.append("Has city/state Pattern")
    if YEARS.search(text):
        reasons.append("Mentions years of experience.")
        
    # Bullet Points
    num_bullets, avg_bullet_len = bullet_stats(text)
    if num_bullets > 2 and 6 <= avg_bullet_len <= 40:
        score += 20
        reasons.append(f"Structured Bullets (count: {num_bullets}, avg_len: {avg_bullet_len:.1f})")
    elif num_bullets > 0:
        score += 8
        reasons.append("Has Bullet Points")
        
    # Pronoun Checks
    first, second, third = pronoun_counts(text)
    if first <= 3:
        score += 8
        reasons.append("Has Limited Number of First Person Pronouns")
    else:
        score -= min(12, first - 3)
        reasons.append(f"High first-person pronouns (I/me/my/mine: {first})")
        
    # Clamp
    score = max(0, min(100, score))
    
    return score, reasons

def validate_jd(text: str):
    score, reasons = jd_score(text)
    if score >= 45:
        verdict = "accept"
        msg = "Appears to be a Valid Job Description"
    elif score >= 30:
        verdict = "review"
        msg = "Possibly a valid job description. Please confirm"
    else:
        verdict = "reject"
        msg = "This does not look like a job description"
        
    return{"score": score, "reasons": reasons, "verdict": verdict, "msg": msg}
    
    

        
    