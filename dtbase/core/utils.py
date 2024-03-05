"""
Utilities (miscellaneous routines) module
"""
import logging
from typing import Optional

import requests

from dtbase.core.constants import CONST_BACKEND_URL as BACKEND_URL
from dtbase.core.constants import (
    DEFAULT_USER_EMAIL,
    DEFAULT_USER_PASS,
)
from dtbase.core.exc import BackendCallError


def backend_call(
    request_type: str,
    end_point_path: str,
    payload: Optional[dict] = None,
    headers: Optional[dict] = None,
) -> requests.Response:
    """Make an API call to the backend server."""
    headers = {} if headers is None else headers
    request_func = getattr(requests, request_type)
    url = f"{BACKEND_URL}{end_point_path}"
    if payload:
        headers = headers | {"content-type": "application/json"}
        response = request_func(url, headers=headers, json=payload)
    else:
        response = request_func(url, headers=headers)
    return response


def login(
    email: str = DEFAULT_USER_EMAIL, password: Optional[str] = DEFAULT_USER_PASS
) -> tuple[str, str]:
    """Log in to the backend server.

    If no user credentials are provided, use the default ones.

    Return an access token and a refresh token.
    """
    if password is None:
        raise ValueError("Must provide a password.")
    response = backend_call(
        "post",
        "/auth/login",
        {"email": DEFAULT_USER_EMAIL, "password": DEFAULT_USER_PASS},
    )
    if response.status_code != 200:
        raise BackendCallError(response)
    access_token = response.json()["access_token"]
    refresh_token = response.json()["refresh_token"]
    return access_token, refresh_token


def auth_backend_call(
    request_type: str,
    end_point_path: str,
    payload: Optional[dict] = None,
    headers: Optional[dict] = None,
    token: Optional[str] = None,
) -> requests.Response:
    """Make an API call to the backend, with authentication.

    If no access token is given, use the `login` function to get one with default
    credentials.
    """
    if token is None:
        token = login()[0]
    if headers is None:
        headers = {}
    headers = headers | {"Authorization": f"Bearer {token}"}
    return backend_call(request_type, end_point_path, payload, headers)


def log_rest_response(response: requests.Response) -> None:
    """
    Logging the response from the backend API
    """
    msg = f"Got response {response.status_code}: {response.text}"
    if 300 > response.status_code:
        logging.info(msg)
    else:
        logging.warning(msg)
