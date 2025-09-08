from fastapi import APIRouter

jobfit_router = APIRouter()

@jobfit_router.get("/")
async def root():
    """
    Root endpoint for the job fitting service.
    
    Returns:
        dict: A dictionary containing a welcome message.
    """
    return {"message": "Welcome to the job fitting service"}



