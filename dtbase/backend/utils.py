import typing as ty
from collections.abc import Container, Mapping
from typing import Generator, Optional, Tuple, Union

from flask import Response, jsonify
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session as SqlaSession
from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.orm.session import sessionmaker

from dtbase.core.utils import connect_db

# We may have to deal with various objects that represent a database connection session,
# so make a union type of all of them. This is used for type annotations around the
# codebase.
Session = scoped_session[SqlaSession] | SqlaSession

DB_ENGINE: Optional[Engine] = None
DB_SESSION_MAKER: Optional[sessionmaker] = None


def create_global_database_connection(
    connection_string: str, database_name: str, reset: bool = False
) -> None:
    global DB_ENGINE, DB_SESSION_MAKER
    if DB_ENGINE is None or reset:
        DB_ENGINE = connect_db(connection_string, database_name)
    if DB_SESSION_MAKER is None or reset:
        DB_SESSION_MAKER = sessionmaker(
            autocommit=False, autoflush=False, bind=DB_ENGINE
        )


def global_session_maker() -> sessionmaker:
    if DB_SESSION_MAKER is None:
        raise ValueError(
            "DB_SESSION_MAKER is not set. "
            "You may need to run create_global_database_connection."
        )
    return DB_SESSION_MAKER


def global_engine() -> Engine:
    if DB_ENGINE is None:
        raise ValueError(
            "DB_ENGINE is not set. "
            "You may need to run create_global_database_connection."
        )
    return DB_ENGINE


def db_session() -> Generator[Session, None, None]:
    session_maker = global_session_maker()
    with session_maker() as session:
        yield session


def set_session_if_unset(session: Optional[Session]) -> Session:
    """Returns a default value for a `session` argument if it isn't set."""
    if session is not None:
        return session
    else:
        raise NotImplementedError("No default session is set.")


T = ty.TypeVar("T")


def check_keys(
    payload: Mapping[T, str], keys: Container[T], api_endpoint: str
) -> Union[Tuple[Response, int], None]:
    """Check if `keys` are in `payload` and return a json response if not.

    Args:
        payload: Dictionary to check.
        keys: List required keys to check for.
        api_endpoint: API endpoint that was called.

    Returns:
        None if all keys are in payload, otherwise a json response with an error.
    """

    missing = [k for k in keys if k not in payload.keys()]
    if missing:
        return (
            jsonify(
                {"error": f"Must include {missing} in POST request to {api_endpoint}."}
            ),
            400,
        )
    return None
