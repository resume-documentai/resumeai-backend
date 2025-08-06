from fastapi import APIRouter, HTTPException, Depends
from app.core.utils import security as auth_utils
from app.core.models.pydantic_models import UserRegister, UserLogin
from app.core.dependencies import get_security_repository
from app.services.security_repository import SecurityRepository

auth_router = APIRouter()

# Root endpoint for the authentication service
@auth_router.get("/")
async def root():
    """
    Root endpoint for the authentication service.
    
    Returns:
        dict: A dictionary containing a welcome message.
    """
    return {"message": "Welcome to the authentication service"}

# Endpoint for user registration
@auth_router.post("/register/")
async def register(
    user: UserRegister,
    security_repository: SecurityRepository = Depends(get_security_repository)):
    """
    Register a new user.
    
    Args:
        user (UserRegister): The user to register.
        db (Database): The database to use for registration.
    
    Returns:
        dict: A dictionary containing a success message.
    """
    # Check if the email is already registered    
    if security_repository.username_exists(user.username):
        raise HTTPException(status_code=400, detail="Username is taken.")
    
    if security_repository.email_exists(user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Register the user
    security_repository.register_user_in_db(user.username, user.email, user.password)
    
    return {"message": "User registered successfully"}

# Endpoint for user login
@auth_router.post("/login/")
async def login(
    user: UserLogin,
    security_repository: SecurityRepository = Depends(get_security_repository)):
    """
    Login a user.
    
    Args:
        user (UserLogin): The user to login.
        db (Database): The database to use for login.
    
    Returns:
        dict: A dictionary containing an access token and user information.
    """
    # Find the user in the database
    db_user = security_repository.get_user(user.username_or_email)
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid email or username")
    
    # Verify the user's password
    if not auth_utils.verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Create a JWT token for the user
    token = auth_utils.create_jwt_token(str(db_user.user_id))
    
    # Return the access token and user information
    return {
        "access_token": token, 
        "user": {
            "user_id": str(db_user.user_id), 
            "username": db_user.username, 
            "email": db_user.email
        }
    }
    
# Sample protected route that requires a valid JWT token
# @auth_router.get("/protected/")
# async def protected_route(token: str = Depends(auth_utils.verify_jwt)):
#     if not token:
#         raise HTTPException(status_code=403, detail="Invalid or expired token")
#     return {"message": "You have access!", "user_id": token}

