from passlib.context import CryptContext
import jwt
from fastapi import HTTPException
import datetime
from app.core.config import JWT_SECRET

# Initialize the password context with bcrypt algorithm
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_jwt_token(user_id: str) -> str:
    to_encode = {
        "sub": user_id,
        "exp": datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(days=1)
    }
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm="HS256")
    return encoded_jwt

def verify_jwt(token: str) -> dict:
    try:
        decoded_jwt = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return decoded_jwt
    except jwt.exceptions.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.exceptions.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
