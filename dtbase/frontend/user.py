from typing import Optional

from flask_login import UserMixin
from requests.models import Response

import dtbase.frontend.exc as exc
from dtbase.core.utils import backend_call

ALL_USERS = {}


class User(UserMixin):
    """Class representing users, as the front end sees them.

    Subclass of flask-login's UserMixin, to provide default implementations of some of
    the methods.
    """

    def __init__(self: "User", email: str) -> None:
        self.email = email
        self.access_token = None
        self.refresh_token = None
        ALL_USERS[email] = self

    def get_id(self: "User") -> str:
        return self.email

    @staticmethod
    def get(email: str) -> "User":
        if email in ALL_USERS:
            user = ALL_USERS[email]
        else:
            user = User(email)
        return user

    def authenticate(self: "User", password: str) -> None:
        response = backend_call(
            "post", "/auth/login", payload={"email": self.email, "password": password}
        )
        if response.status_code != 200:
            raise exc.AuthorizationError("Invalid credentials.")
        try:
            self.access_token = response.json()["access_token"]
            self.refresh_token = response.json()["refresh_token"]
        except KeyError:
            raise exc.BackendApiError("Malformed response from /auth/login")

    def refresh(self: "User") -> None:
        response = backend_call(
            "post",
            "/auth/refresh",
            headers={"Authorization": f"Bearer {self.refresh_token}"},
        )
        if response.status_code != 200:
            self.access_token = None
            self.refresh_token = None
            raise exc.AuthorizationError("Invalid refresh token.")
        try:
            self.access_token = response.json()["access_token"]
            self.refresh_token = response.json()["refresh_token"]
        except KeyError:
            raise exc.BackendApiError("Malformed response from /auth/refresh")

    @property
    def is_authenticated(self: "User") -> bool:
        return self.access_token is not None

    def backend_call(
        self: "User",
        request_type: str,
        end_point_path: str,
        payload: Optional[dict] = None,
        headers: Optional[dict] = None,
    ) -> Response:
        headers = {} if headers is None else headers
        if not self.is_authenticated:
            raise exc.AuthorizationError(
                "An unautheticated user tried to make a backend call to "
                f"{end_point_path}"
            )
        response = backend_call(
            request_type,
            end_point_path,
            payload=payload,
            headers=headers | {"Authorization": f"Bearer {self.access_token}"},
        )
        # If the access token has expired, refresh it and try again
        if response.status_code == 401 and response.json == {
            "msg": "Token has expired"
        }:
            self.refresh()
            response = backend_call(
                request_type,
                end_point_path,
                payload=payload,
                headers=headers | {"Authorization": f"Bearer {self.access_token}"},
            )
        return response
