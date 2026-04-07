import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import logging

from fastapi import APIRouter, HTTPException
from src.backend.api.schemas.auth import LoginRegisterRequest, TokenResponse

from passlib.context import CryptContext
from jose import jwt

from src.backend.api.initialize import service_connections
import src.backend.database.repository.users as users_repository

database = service_connections.get_connection()

router = APIRouter(prefix="/auth")
logger = logging.getLogger(__name__)

load_dotenv()
SECRET_KEY = os.getenv('JWT_KEY')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

pwd_context = CryptContext(
    schemes=["bcrypt"]
)


@router.post("/register", status_code=201)
async def register(user: LoginRegisterRequest):
    if users_repository.get_user_by_username(database, user.login):
        raise HTTPException(status_code=409,
                            detail={"message": "Username already taken"}
                            )
    password_hash = hash_password(user.password)
    try:
        users_repository.create_user(database, user.login, password_hash)
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500,
                            detail={"message": "Internal server error"})
    return {"message": "User registered"}

'''
JWT Tokens are created with user id, to get the user id do:
payload = jwt.decode(token, SECRET_KEY, algorithm=ALGORITHM)
id = payload.get("sub")

Also check expiry prolly
'''


@router.post("/login", response_model=TokenResponse)
async def login(user: LoginRegisterRequest):
    try:
        db_user = users_repository.get_user_by_username(database, user.login)
        if not db_user:
            raise HTTPException(status_code=401,
                                detail={"message": "Invalid credentials"})
        hashed_password = db_user.password_hash
        if not verify_password(user.password, hashed_password):
            raise HTTPException(status_code=401,
                                detail={"message": "Invalid credentials"})
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500,
                            detail={"message": "Internal server error"})
    access_token = create_jwt_token(
        data={"sub": db_user.id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return TokenResponse(jwt_token=access_token)


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_jwt_token(data: dict, expires_delta: timedelta = timedelta(days=7)):
    to_encode = data.copy()
    expire = datetime.now() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
