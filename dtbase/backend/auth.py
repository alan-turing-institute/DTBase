"""
Module (routes.py) to handle API endpoints related to authentication
"""
import datetime as dt

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError
from sqlalchemy.orm import Session

from dtbase.backend.models import ParsedToken, TokenPair
from dtbase.backend.utils import db_session
from dtbase.core import users
from dtbase.core.constants import (
    JWT_ACCESS_TOKEN_EXPIRES,
    JWT_REFRESH_TOKEN_EXPIRES,
    JWT_SECRET_KEY,
)

JWT_ALGORITHM = "HS256"

# Creating tokens


def _create_access_token(data: dict, expires_delta: dt.timedelta) -> str:
    to_encode = data.copy()
    expire = dt.datetime.now(dt.timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    if JWT_SECRET_KEY is None:
        raise ValueError("JWT_SECRET_KEY is not set")
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def create_token_pair(email: str) -> TokenPair:
    """Create a new authentication token pair for a user."""
    access_token = _create_access_token(
        {"sub": email, "token_type": "access"}, expires_delta=JWT_ACCESS_TOKEN_EXPIRES
    )
    refresh_token = _create_access_token(
        {"sub": email, "token_type": "refresh"}, expires_delta=JWT_REFRESH_TOKEN_EXPIRES
    )
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


# Authenticating tokens

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def _authenticate_token(
    token: str = Depends(oauth2_scheme), session: Session = Depends(db_session)
) -> ParsedToken:
    """Get the authentication token and validate it.

    Checks that the token belongs to a valid user and isn't expired.

    Args:
        token (str): The authentication token.
        session (Session): The database session.

    Returns:
        dict: The payload of the token.

    Raises:
        ValueError: If JWT_SECRET_KEY is not set.
        HTTPException: If the token is invalid.
    """
    if JWT_SECRET_KEY is None:
        raise ValueError("JWT_SECRET_KEY is not set")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            require=["exp", "sub", "token_type"],
        )
        print(payload)
        parsed_token = ParsedToken(**payload)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
        )
    except (jwt.InvalidTokenError, ValidationError):
        raise credentials_exception
    if not users.user_exists(parsed_token.sub, session=session):
        raise credentials_exception
    return parsed_token


def authenticate_access(
    parsed_token: ParsedToken = Depends(_authenticate_token),
) -> ParsedToken:
    """Check that a token is a valid access token.

    Raise an error if not, return the parsed token.
    """
    if parsed_token.token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token of wrong type",
        )
    return parsed_token


def authenticate_refresh(
    parsed_token: ParsedToken = Depends(_authenticate_token),
) -> ParsedToken:
    """Check that a token is a valid refresh token.

    Raise an error if not, return the parsed token.
    """
    if parsed_token.token_type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token of wrong type",
        )
    return parsed_token
