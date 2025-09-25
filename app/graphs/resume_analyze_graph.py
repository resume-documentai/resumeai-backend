from langgraph.graph import StateGraph, END
from typing import Optional, TypedDict, List
from app.services.file_processing import FileProcessing
from app.services.llm_prompts import DOCUMENT_TEMPLATE, BASE_PROMPT
from app.services.data_prep import DataPrep
from app.services.resume_repository import ResumeRepository
from app.services.process_llm import ProcessLLM
from app.core.models.pydantic_models import Feedback

"""
Pre Validation Analysis Graph:

    extract_text
    |-> extract_skills
    |-> extract_experiences
    |-> generate_feedback 
        v
    merge_all
        v
    generate_resume_embedding
        v
    finalize

Output for user: highlighted text, feedback
Output for validation: text, skills, experiences

"""
class ResumeState(TypedDict, total=False):
    file_id: str
    file_ext: str
    temp_path: str
    file_processing: FileProcessing
    process_llm: ProcessLLM
    model_option: str
    resume_repository: ResumeRepository
    user_id: Optional[str]
    file_name: Optional[str]

    # Intermediate Outputs
    text: Optional[str]
    skills: Optional[List[str]]
    experiences: Optional[List]
    feedback: Optional[str]
    embedding: Optional[List[float]]
    highlighted_text: Optional[str]
    llm_feedback: Optional[str]

    # Skip Logic
    already_processed: Optional[bool]
    

def extract_text_node(state):
    file_ext: str = state["file_ext"]
    file_processing: FileProcessing = state["file_processing"]
    
    txt = file_processing.extract(state["temp_path"], file_ext)
    state["text"] = txt
    
    return state

def extract_skills_node(state):
    text = state["text"]
    state["skills"] = DataPrep.extract_skills(text)
    
    return {"skills": state["skills"]}

def extract_experiences_node(state):
    text = state["text"]
    state["experiences"] = DataPrep.extract_experiences(text)
    
    return {"experiences": state["experiences"]}

def check_if_resume_processed_node(state):
    resume_repository: ResumeRepository = state["resume_repository"]
    if state["user_id"]:
        resume = resume_repository.get_resume(state["file_id"])
        if resume:
            state["already_processed"] = True
            state["highlighted_text"] = resume.resume_text
            state["llm_feedback"] = Feedback(**resume.feedback.feedback)
        else:
            state["already_processed"] = False

    return state

def generate_feedback_node(state):
    document = DOCUMENT_TEMPLATE.format(
        document=state["text"],
        feedback={},
        chat_history=""
    )
    
    feedback = state["process_llm"].process(
        document,
        model=state["model_option"],
        prompt=BASE_PROMPT
    )
    state["feedback"] = feedback
    
    return state

def merge_all(state):
    if not all([
        state.get("skills"),
        state.get("experiences"),
        state.get("feedback") or state.get("llm_feedback"),
    ]):
        raise ValueError("Waiting on branches to finish.")
    
    return state

def get_existing_resume_embedding_node(state):
    resume_repository: ResumeRepository = state["resume_repository"]
    state["embedding"] = resume_repository.get_resume_embedding(state["file_id"])
    return state

def generate_resume_embedding_node(state):
    text = state["text"]
    state["embedding"] = state["file_processing"].generate_embeddings(text)
    
    return state

def finalize_and_save_node(state):
    if not state.get("highlighted_text") and not state.get("llm_feedback"):
        text = state["text"]
        state["highlighted_text"], state["llm_feedback"] = DataPrep.prep_output(text, state["feedback"])
    
    resume_repository: ResumeRepository = state["resume_repository"]
    
    resume_repository.save_resume_feedback(
        user_id=state["user_id"],
        file_id=state["file_id"],
        file_name=state["file_name"],
        resume_text=state["highlighted_text"],
        feedback=state["llm_feedback"],
        embedding=state["embedding"]
    )    
    
    return state


# ---- Build the Graph ----
builder = StateGraph(ResumeState)
builder.add_node("extract_text", extract_text_node)
builder.add_node("check_if_resume_processed", check_if_resume_processed_node)
builder.add_node("extract_skills", extract_skills_node)
builder.add_node("extract_experiences", extract_experiences_node)
builder.add_node("generate_feedback", generate_feedback_node)
builder.add_node("merge_all", merge_all)
builder.add_node("get_existing_resume_embedding", get_existing_resume_embedding_node)
builder.add_node("generate_resume_embedding", generate_resume_embedding_node)
builder.add_node("finalize_and_save", finalize_and_save_node)

builder.set_entry_point("extract_text")

# ---- Edges ----


builder.add_edge("extract_text", "extract_skills")
builder.add_edge("extract_skills", "extract_experiences")
builder.add_edge("extract_experiences", "check_if_resume_processed")
builder.add_conditional_edges(
    "check_if_resume_processed",
    lambda state: "merge_all" if state["already_processed"] else "generate_feedback",
)

builder.add_edge("generate_feedback", "merge_all")

builder.add_conditional_edges(
    "merge_all",
    lambda state: "get_existing_resume_embedding" if state["already_processed"] else "generate_resume_embedding"
)

builder.add_edge("get_existing_resume_embedding", "finalize_and_save")
builder.add_edge("generate_resume_embedding", "finalize_and_save")
builder.add_edge("finalize_and_save", END)

resume_analyze_graph = builder.compile()