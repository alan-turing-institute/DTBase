from pydantic import BaseModel


class MessageResponse(BaseModel):
    detail: str


class UserIdentifier(BaseModel):
    email: str


class LoginCredentials(BaseModel):
    email: str
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str


class ParsedToken(BaseModel):
    sub: str
    exp: int
    token_type: str
