"""
Test the functions for accessing the user table.
"""
import pytest
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.orm import Session

from dtbase.core import users

# Some example values used for testing.
EMAIL = "hubby@hobbob.bubbly"
PASSWORD = "iknowsecurity"


def insert_user(session: Session) -> None:
    """Insert a user into the database."""
    users.insert_user(EMAIL, PASSWORD, session=session)


def test_insert_user(session: Session) -> None:
    """Test inserting users."""
    insert_user(session)


def test_insert_user_duplicate(session: Session) -> None:
    """Test inserting users."""
    insert_user(session)
    error_msg = 'duplicate key value violates unique constraint "User_email_key"'
    with pytest.raises(IntegrityError, match=error_msg):
        insert_user(session)


def test_check_password(session: Session) -> None:
    """Test checking a user's password."""
    insert_user(session)
    assert users.check_password(EMAIL, PASSWORD, session=session)


def test_check_password_wrong(session: Session) -> None:
    """Test giving the wrong password."""
    insert_user(session)
    assert not users.check_password(EMAIL, "whoooops", session=session)


def test_check_password_nonexistent(session: Session) -> None:
    """Test checking a non-existent user's password."""
    assert not users.check_password(
        "bigfoot@northdakota.gov", PASSWORD, session=session
    )


def test_change_password(session: Session) -> None:
    """Test changing a user's password."""
    insert_user(session)
    new_password = "new password is better"
    users.change_password(EMAIL, new_password, session=session)
    assert not users.check_password(EMAIL, PASSWORD, session=session)
    assert users.check_password(EMAIL, new_password, session=session)


def test_change_password_nonexistent(session: Session) -> None:
    """Test changing a non-existent user's password."""
    new_password = "new password is better"
    error_msg = "No row was found"
    with pytest.raises(NoResultFound, match=error_msg):
        users.change_password(EMAIL, new_password, session=session)


def test_delete_user(session: Session) -> None:
    """Try to delete a non-existent user."""
    insert_user(session)
    users.delete_user(EMAIL, session=session)
    # This user shouldn't exist any more
    assert not users.check_password(EMAIL, PASSWORD, session=session)


def test_delete_user_nonexistent(session: Session) -> None:
    """Try to delete a non-existent user."""
    error_msg = "No user 'BLAHBLAH'"
    with pytest.raises(ValueError, match=error_msg):
        users.delete_user("BLAHBLAH", session=session)
