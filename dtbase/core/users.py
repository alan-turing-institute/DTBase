"""Functions for accessing the user table. """
import sqlalchemy as sqla
from sqlalchemy.orm import Session

from dtbase.backend.utils import add_default_session
from dtbase.core.structure import User


@add_default_session
def insert_user(email: str, password: str, session: Session) -> None:
    """
    Add a new user to the database.

    Args:
        email: Email address by which we'll identify this user
        password: The password
        session: SQLAlchemy session. Optional.

    Returns:
        None
    """
    new_user = User(password=password, email=email)
    session.add(new_user)
    session.flush()


@add_default_session
def delete_user(email: str, session: Session) -> None:
    """
    Delete a user from the database.

    Args:
        email: The user's email
        session: SQLAlchemy session. Optional.

    Returns:
        None
    """
    result = session.execute(sqla.delete(User).where(User.email == email))
    if result.rowcount == 0:
        raise ValueError(f"No user '{email}'")


@add_default_session
def check_password(email: str, password: str, session: Session) -> bool:
    """
    Check that the email and password combination is valid.

    Args:
        email: Email to look up in the database
        password: Password to check
        session: SQLAlchemy session. Optional.

    Returns:
        True if the user exists and the password is correct False otherwise
    """
    user = session.execute(sqla.select(User).where(User.email == email)).scalar()
    if not user:
        # This user does not exist.
        return False
    return user.check_password(password)


@add_default_session
def change_password(email: str, password: str, session: Session) -> None:
    """Change the password of a given user.

    Args:
        email: User whose password to change
        password: The new password
        session: SQLAlchemy session. Optional.

    Returns:
        None
    """
    user = session.execute(sqla.select(User).where(User.email == email)).one()[0]
    user.password = password
    session.flush()
