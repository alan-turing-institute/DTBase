"""Functions for accessing the user table. """
from typing import List, Optional

import sqlalchemy as sqla

from dtbase.backend.utils import Session, set_session_if_unset
from dtbase.core.structure import User


def user_exists(email: str, session: Optional[Session] = None) -> bool:
    """
    Check that a user with the given email exists.

    Args:
        email: Email address to check
        session: SQLAlchemy session. Optional.

    Returns:
        True if the user exists, False otherwise
    """
    session = set_session_if_unset(session)
    rows = session.execute(
        sqla.select(User.email).where(User.email == email)
    ).fetchall()
    return len(rows) > 0


def list_users(session: Optional[Session] = None) -> List[str]:
    """
    List all users in the database

    Args:
        session: SQLAlchemy session. Optional.

    Returns:
        A list of user emails.
    """
    session = set_session_if_unset(session)
    rows = session.execute(sqla.select(User.email)).fetchall()
    emails = [r[0] for r in rows]
    return emails


def insert_user(email: str, password: str, session: Optional[Session] = None) -> None:
    """
    Add a new user to the database.

    Args:
        email: Email address by which we'll identify this user
        password: The password
        session: SQLAlchemy session. Optional.

    Returns:
        None
    """
    session = set_session_if_unset(session)
    new_user = User(password=password, email=email)
    session.add(new_user)
    session.flush()


def delete_user(email: str, session: Optional[Session] = None) -> None:
    """
    Delete a user from the database.

    Args:
        email: The user's email
        session: SQLAlchemy session. Optional.

    Returns:
        None
    """
    session = set_session_if_unset(session)
    result = session.execute(sqla.delete(User).where(User.email == email))
    if result.rowcount == 0:
        raise ValueError(f"No user '{email}'")


def check_password(
    email: str, password: str, session: Optional[Session] = None
) -> bool:
    """
    Check that the email and password combination is valid.

    Args:
        email: Email to look up in the database
        password: Password to check
        session: SQLAlchemy session. Optional.

    Returns:
        True if the user exists and the password is correct False otherwise
    """
    session = set_session_if_unset(session)
    user = session.execute(sqla.select(User).where(User.email == email)).scalar()
    if not user:
        # This user does not exist.
        return False
    return user.check_password(password)


def change_password(
    email: str, password: str, session: Optional[Session] = None
) -> None:
    """Change the password of a given user.

    Args:
        email: User whose password to change
        password: The new password
        session: SQLAlchemy session. Optional.

    Returns:
        None
    """
    session = set_session_if_unset(session)
    user = session.execute(sqla.select(User).where(User.email == email)).one()[0]
    user.password = password
    session.flush()
