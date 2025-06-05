# ResumeAI Backend

The backend service for ResumeAI, a platform that helps users analyze and improve their resumes using AI.

## Overview

This backend service provides RESTful APIs for resume processing, authentication, and chat functionality. It's built using FastAPI and includes the following main components:

### Docker Setup

The project uses Python 3.9 and includes several system dependencies for building and running the application. The Docker setup is recommended for consistent development and deployment.

1. Build the Docker image:
   ```bash
   docker build -t resumeai-backend .
   ```

2. Run the container:
   ```bash
   docker run -p 8000:8000 resumeai-backend
   ```

3. The container will:
   - Install system dependencies (build-essential, cmake, etc.)
   - Install Python packages from requirements.txt
   - Copy application code
   - Run the entrypoint script

4. Access the application:
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

5. Environment Variables:
   - Copy `.env.example` to `.env` with your configuration
   - The container will automatically use the `.env` file

6. Development with Docker:
   ```bash
   # Build with development tag
   docker build -t resumeai-backend:dev --target dev .

   # Run with volume mount for hot reloading
   docker run -v $(pwd):/app -p 8000:8000 resumeai-backend:dev
   ```

### Key Services

1. **Resume Processing**
   - API endpoints for uploading and processing resumes
   - Document analysis and extraction capabilities

2. **Authentication**
   - User authentication and authorization system
   - Secure API access control

3. **Chat Integration**
   - Chat functionality for user interactions
   - Integration with AI chat capabilities

## Tech Stack

**Backend**
- FastAPI
- pdfminer
- python-docx
- OpenAI API
- LLAMA
- MongoDB
- FastAPI JWT Auth
- Python Dotenv
- LangChain Community Embeddings