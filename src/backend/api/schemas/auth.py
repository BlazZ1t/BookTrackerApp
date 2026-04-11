from pydantic import BaseModel


class LoginRegisterRequest(BaseModel):
    login: str
    password: str


class TokenResponse(BaseModel):
    jwt_token: str
    token_type: str = "bearer"
