from typing import Optional

import requests

from dtbase.core.constants import DEFAULT_USER_EMAIL, DEFAULT_USER_PASS
from dtbase.core.exc import BackendCallError
from dtbase.core.utils import backend_call


def login() -> str:
    response = backend_call(
        "post",
        "/auth/login",
        {"email": DEFAULT_USER_EMAIL, "password": DEFAULT_USER_PASS},
    )
    if response.status_code != 200:
        raise BackendCallError(response)
    token = response.json()["access_token"]
    return token


def auth_backend_call(
    request_type: str,
    end_point_path: str,
    payload: Optional[dict] = None,
    headers: Optional[dict] = None,
    token: Optional[str] = None,
) -> requests.models.Response:
    if token is None:
        token = login()
    if headers is None:
        headers = {}
    headers = headers | {"Authorization": f"Bearer {token}"}
    return backend_call(request_type, end_point_path, payload, headers)
