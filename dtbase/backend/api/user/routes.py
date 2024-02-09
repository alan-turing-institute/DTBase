"""
Module (routes.py) to handle API endpoints related to user management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.orm import Session

from dtbase.backend.auth import authenticate_access
from dtbase.backend.models import LoginCredentials, MessageResponse, UserIdentifier
from dtbase.backend.utils import db_session
from dtbase.core import users

router = APIRouter(
    prefix="/user", tags=["user"], dependencies=[Depends(authenticate_access)]
)


@router.get("/list-users", status_code=status.HTTP_200_OK)
def list_users(session: Session = Depends(db_session)) -> list[str]:
    """List all users."""
    emails = users.list_users(session=session)
    return emails


@router.post("/create-user", status_code=status.HTTP_201_CREATED)
def create_user(
    credentials: LoginCredentials, session: Session = Depends(db_session)
) -> MessageResponse:
    """
    Create a new user.

    POST request should have json data (mimetype "application/json") containing
    {
      "email": <type_email:str>,
      "password": <type_password:str>
    }

    Returns 409 if user already exists, otherwise 201.
    """
    email = credentials.email
    password = credentials.password
    try:
        users.insert_user(email, password, session=session)
        session.commit()
    except IntegrityError:
        raise HTTPException(status_code=409, detail="User already exists")
    return MessageResponse(detail="User created")


@router.post("/delete-user", status_code=status.HTTP_200_OK)
def delete_user(
    user_id: UserIdentifier, session: Session = Depends(db_session)
) -> MessageResponse:
    """Delete a user."""
    try:
        users.delete_user(user_id.email, session=session)
        session.commit()
    except ValueError:
        raise HTTPException(status_code=400, detail="User doesn't exist")
    return MessageResponse(detail="User deleted")


@router.post("/change-password", status_code=status.HTTP_200_OK)
def change_password(
    credentials: LoginCredentials, session: Session = Depends(db_session)
) -> MessageResponse:
    """Change a user's password."""
    email = credentials.email
    password = credentials.password
    try:
        users.change_password(email, password, session=session)
        session.commit()
    except NoResultFound:
        raise HTTPException(status_code=400, detail="User doesn't exist")
    return MessageResponse(detail="Password changed")
