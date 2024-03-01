"""
Module (routes.py) to handle API endpoints related to authentication
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from dtbase.backend.auth import authenticate_refresh, create_token_pair
from dtbase.backend.db import db_session
from dtbase.backend.models import (
    LoginCredentials,
    MessageResponse,
    ParsedToken,
    TokenPair,
)
from dtbase.core import users

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_401_UNAUTHORIZED: {"model": MessageResponse}},
)
def login(
    credentials: LoginCredentials, session: Session = Depends(db_session)
) -> TokenPair:
    """Generate a new authentication token."""
    email = credentials.email
    password = credentials.password
    valid_login = users.check_password(email, password, session=session)
    if not valid_login:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    return create_token_pair(email)


@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_401_UNAUTHORIZED: {"model": MessageResponse}},
)
def refresh(parsed_token: ParsedToken = Depends(authenticate_refresh)) -> TokenPair:
    """
    Refresh an authentication token.

    Returns output similar to `/auth/login`, only the authentication method is different
    (checking the validity of a refresh token rather than email and password).
    """
    email = parsed_token.sub
    return create_token_pair(email)
