import typing as ty
from collections.abc import Container, Mapping
from typing import Optional, Tuple, Union

from flask import Response, jsonify
from flask_sqlalchemy.session import Session as FlaskSqlaSession
from sqlalchemy.orm import Session as SqlaSession
from sqlalchemy.orm.scoping import scoped_session

from dtbase.core.structure import SQLA as db

# We may have to deal with various objects that represent a database connection session,
# so make a union type of all of them.
Session = (
    scoped_session[SqlaSession]
    | scoped_session[FlaskSqlaSession]
    | FlaskSqlaSession
    | SqlaSession
)


def default_session(
    session: Optional[Session],
) -> Session:
    """Utility function that returns a default value for a `session` argument."""
    return session if session is not None else db.session


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
