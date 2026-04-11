from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from src.backend.api.routes.auth import SECRET_KEY, ALGORITHM

security = HTTPBearer()


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Decode JWT Bearer token and return the authenticated user_id"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail={"message": "Invalid token: missing subject"},
            )
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail={"message": "Invalid or expired token"},
        )
    return user_id
