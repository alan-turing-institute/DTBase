from flask_login import UserMixin

import dtbase.webapp.exc as exc
import dtbase.webapp.utils as utils

ALL_USERS = {}


class User(UserMixin):
    """Class representing users, as the front end sees them.

    Subclass of flask-login's UserMixin, to provide default implementations of some of
    the methods.
    """

    def __init__(self, email):
        self.email = email
        self.access_token = None
        self.refresh_token = None
        ALL_USERS[email] = self

    def get_id(self):
        return self.email

    @classmethod
    def get(cls, email):
        if email in ALL_USERS:
            user = ALL_USERS[email]
        else:
            user = User(email)
        return user

    def authenticate(self, password):
        response = utils.backend_call(
            "post", "/auth/login", payload={"email": self.email, "password": password}
        )
        if response.status_code != 200:
            raise exc.AuthorizationError("Invalid credentials.")
        try:
            self.access_token = response.json()["access_token"]
            self.refresh_token = response.json()["refresh_token"]
        except KeyError:
            raise exc.BackendApiError("Malformed response from /auth/login")

    def refresh(self):
        response = utils.backend_call(
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
    def is_authenticated(self):
        return self.access_token is not None

    def backend_call(self, request_type, end_point_path, payload=None, headers=None):
        headers = {} if headers is None else headers
        if not self.is_authenticated:
            raise exc.AuthorizationError(
                "An unautheticated user tried to make a backend call to "
                f"{end_point_path}"
            )
        response = utils.backend_call(
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
            response = utils.backend_call(
                request_type,
                end_point_path,
                payload=payload,
                headers=headers | {"Authorization": f"Bearer {self.access_token}"},
            )
        if 500 > response.status_code >= 400:
            raise exc.BackendApiError(
                f"A request to {end_point_path} with payload "
                f"{payload} returned {response}, {response.json()}."
            )
        return response
