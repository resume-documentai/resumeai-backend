from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.routes.resume import resume_router
from app.api.v1.routes.chat import chat_router
from app.api.v1.routes.auth import auth_router
from app.core.database import database


async def lifespan(app: FastAPI):
    # Initialize database connection
    database.initialize()
    yield
    database.close()

app = FastAPI(lifespan=lifespan, redirect_slashes=False)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(resume_router, prefix="/resumes", tags=["Resumes"])
app.include_router(chat_router, prefix="/chat", tags=["Chat"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Resume Reviewer API"}




