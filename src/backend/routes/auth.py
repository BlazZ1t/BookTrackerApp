import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException
from models.auth import LoginRegisterRequest, TokenResponse

import hashlib
from passlib.context import CryptContext
from jose import jwt


database_found_user = False  # TODO: Replace with actual database call

router = APIRouter(prefix="/auth")

load_dotenv()
SECRET_KEY = os.getenv('JWT_KEY')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

pwd_context = CryptContext(
    schemes=["bcrypt"]
)


@router.post("/register", status_code=201)
async def register(user: LoginRegisterRequest):
    # login_hash = hash_username(user.login)
    if database_found_user:
        raise HTTPException(status_code=409,
                            detail={"message": "Username already taken"}
                            )
    # password_hash = hash_password(user.password)
    # TODO: Add actual database saving
    return {"message": "User registered"}


@router.post("/login", response_model=TokenResponse)
async def login(user: LoginRegisterRequest):
    if not database_found_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    hashed_password = ""  # TODO: Add pulling data from database
    hashed_username = ""  # TODO: Add pulling data from database
    if not verify_password(user.password, hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_jwt_token(
        data={"sub": hashed_username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return TokenResponse(access_token=access_token)


def hash_username(username: str):
    return hashlib.sha256(username.encode()).hexdigest()[:32]


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_jwt_token(data: dict, expires_delta: timedelta = timedelta(days=7)):
    to_encode = data.copy()
    expire = datetime.now() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
