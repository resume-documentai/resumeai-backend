from app.services.data_prep import DataPrep
from app.core.models.pydantic_models import Feedback, FeedbackCategory


def test_clean_text_success():
    """Test basic text cleaning with extra newlines"""
    text = "This is a test\n\n\n"
    expected = "This is a test"
    assert DataPrep.clean_text(text) == expected


def test_clean_text_empty():
    """Test cleaning empty text"""
    assert DataPrep.clean_text("") == ""


def test_clean_text_whitespace_only():
    """Test cleaning whitespace-only text"""
    assert DataPrep.clean_text("   \n\n\n  ") == ""


def test_clean_text_with_bullet_points():
    """Test text with bullet points"""
    text = "\n + First point\n• Second point"
    expected = "* First point\n* Second point"
    assert DataPrep.clean_text(text) == expected


def test_clean_text_with_headers():
    """Test text with headers"""
    text = "EXPERIENCE\nJob Title\n• Did something"
    expected = "EXPERIENCE\nJob Title\n* Did something"
    assert DataPrep.clean_text(text) == expected


def test_clean_text_with_multiple_paragraphs():
    """Test text with multiple paragraphs"""
    text = "First paragraph.\n\nSecond paragraph. Still second.\n\nThird paragraph."
    expected = "First paragraph.\nSecond paragraph. Still second.\nThird paragraph."
    assert DataPrep.clean_text(text) == expected


def test_clean_text_with_sentence_splitting():
    """Test proper sentence splitting and joining"""
    text = "* A bullet point with a new line in between\n\nthat ends here.\nNew paragraph."
    expected = "* A bullet point with a new line in between that ends here.\nNew paragraph."
    assert DataPrep.clean_text(text) == expected


def test_clean_text_with_mixed_content():
    """Test with mixed content including bullets, headers, and regular text"""
    text = """
    SUMMARY
    • First point
    • Second point
    
    EXPERIENCE
    Job Title
    • Did something
    • Did something else
    """
    expected = "SUMMARY\n* First point\n* Second point\nEXPERIENCE\nJob Title\n* Did something\n* Did something else"
    assert DataPrep.clean_text(text).strip() == expected.strip()


def test_highlight_text_match():
    """Test highlighting matching text"""
    text = "This is a test"
    match = "test"
    color = "bg-yellow-300"
    expected = 'This is a <mark class=\'bg-yellow-300\'>test</mark>'
    assert DataPrep.highlight_text(text, match, color) == expected

def test_highlight_text_no_match():
    """Test highlighting when there's no match"""
    text = "This is a test"
    match = "no-match"
    color = "bg-yellow-300"
    assert DataPrep.highlight_text(text, match, color) == text

def test_prep_output_success():
    """Test preparing output with valid feedback"""
    text = "This is a test resume"
    feedback = {
        "structure_organization": {
            "score": 4.5,
            "strengths": ["Good structure"],
            "weaknesses": ["Could improve formatting"],
            "suggestions": [{"text": "Add more sections", "match": "test"}]
        },
        "clarity_conciseness": {
            "score": 4.0,
            "strengths": ["Clear language"],
            "weaknesses": ["Some redundancy"],
            "suggestions": []
        },
        "grammar_spelling": {
            "score": 5.0,
            "strengths": ["No errors found"],
            "weaknesses": [],
            "suggestions": []
        },
        "impact_accomplishments": {
            "score": 3.5,
            "strengths": ["Good examples"],
            "weaknesses": ["Needs more metrics"],
            "suggestions": []
        },
        "ats_readability": {
            "score": 4.0,
            "strengths": ["Good keywords"],
            "weaknesses": ["Could optimize more"],
            "suggestions": []
        },
        "general_feedback": "Overall good resume"
    }

    result_text, result_feedback = DataPrep.prep_output(text, feedback)
    
    # Check the text was processed
    assert "<mark" in result_text  
    assert ">test</mark>" in result_text
    # Check feedback structure
    assert isinstance(result_feedback, Feedback)
    assert result_feedback.overall_score == 4.2  # (4.5 + 4.0 + 5.0 + 3.5 + 4.0) / 5
    assert result_feedback.general_feedback == "Overall good resume"
    
    # Check one of the categories
    assert hasattr(result_feedback, "structure_organization")
    assert isinstance(result_feedback.structure_organization, FeedbackCategory)
    assert result_feedback.structure_organization.score == 4.5

def test_prep_output_error_handling():
    """Test error handling in prep_output"""
    text = "Test text"
    feedback = {"invalid": "data"} 
    
    result_text, result_feedback = DataPrep.prep_output(text, feedback)
    
    assert result_text == text  
    assert result_feedback is None