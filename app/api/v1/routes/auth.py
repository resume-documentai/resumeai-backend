from fastapi import APIRouter, HTTPException, Depends
from app.core.database import Database
from app.core.utils import security as auth_utils
from app.core.utils.models import UserRegister, UserLogin

auth_router = APIRouter()

# Root endpoint for the authentication service
@auth_router.get("/")
async def root():
    return {"message": "Welcome to the authentication service"}

# Endpoint for user registration
@auth_router.post("/register/")
async def register(user: UserRegister, db: Database = Depends(Database)):
    print("hit", user)
    # Check if the email is already registered
    if db.users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    # Hash the user's password
    hashed_password = auth_utils.hash_password(user.password)
    
    # Create a new user document
    new_user = {
        "username": user.username,
        "email": user.email, 
        "password": hashed_password
    }
    
    # Insert the new user into the database
    db.users_collection.insert_one(new_user)
    
    return {"message": "User registered successfully"}

# Endpoint for user login
@auth_router.post("/login/")
async def login(user: UserLogin, db: Database = Depends(Database)):
    # Find the user in the database
    db_user = db.users_collection.find_one({"email": user.email})
    # Verify the user's password
    if not db_user or not auth_utils.verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create a JWT token for the user
    token = auth_utils.create_jwt_token(str(db_user["_id"]))
    
    # Return the access token and user information
    return {"access_token": token, "user": {"user_id": str(db_user["_id"]), "username": db_user["username"], "email": db_user["email"]}}

# Sample protected route that requires a valid JWT token
# @auth_router.get("/protected/")
# async def protected_route(token: str = Depends(auth_utils.verify_jwt)):
#     if not token:
#         raise HTTPException(status_code=403, detail="Invalid or expired token")
#     return {"message": "You have access!", "user_id": token}

