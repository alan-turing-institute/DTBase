"""
Test API endpoints for users
"""
from collections.abc import Collection

import pytest
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from dtbase.core.constants import DEFAULT_USER_EMAIL
from dtbase.tests.conftest import AuthenticatedClient, check_for_docker
from dtbase.tests.utils import TEST_USER_EMAIL, assert_unauthorized, can_login

DOCKER_RUNNING = check_for_docker()


# Some example values used for testing.
EMAIL = "hubby@hobbob.bubbly"
PASSWORD = "iknowsecurity"


def create_user(client: FlaskClient) -> TestResponse:
    """Create a user to test against."""
    type_data = {"email": EMAIL, "password": PASSWORD}
    response = client.post("/user/create-user", json=type_data)
    return response


def assert_list_users(client: FlaskClient, users: Collection[str]) -> None:
    """Assert that the `/user/list-users` end point returns successfully, and that it
    returns exactly the users provided in the second arguments.
    """
    response = client.get("/user/list-users")
    assert response.status_code == 200
    assert response.json is not None
    assert set(response.json) == set(users)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_create_user(auth_client: AuthenticatedClient) -> None:
    with auth_client as client:
        response = create_user(client)
        assert response.status_code == 201
        assert response.json == {"message": "User created"}
        assert_list_users(client, {TEST_USER_EMAIL, DEFAULT_USER_EMAIL, EMAIL})
        assert can_login(client, email=EMAIL, password=PASSWORD)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_create_user_duplicate(auth_client: AuthenticatedClient) -> None:
    with auth_client as client:
        create_user(client)
        response = create_user(client)
        assert response.status_code == 409
        assert response.json == {"message": "User already exists"}


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_delete_user(auth_client: AuthenticatedClient) -> None:
    with auth_client as client:
        create_user(client)
        payload = {"email": EMAIL, "password": PASSWORD}
        response = client.delete("/user/delete-user", json=payload)
        assert response.status_code == 200
        assert response.json == {"message": "User deleted"}
        assert_list_users(client, {TEST_USER_EMAIL, DEFAULT_USER_EMAIL})


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_delete_user_nonexistent(auth_client: AuthenticatedClient) -> None:
    with auth_client as client:
        response = client.delete(
            "/user/delete-user", json={"email": EMAIL, "password": PASSWORD}
        )
        assert response.status_code == 400
        assert response.json == {"message": "User doesn't exist"}


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_change_password(auth_client: AuthenticatedClient) -> None:
    with auth_client as client:
        create_user(client)
        new_password = "new kids on the block"
        response = client.post(
            "/user/change-password", json={"email": EMAIL, "password": new_password}
        )
        assert response.status_code == 200
        assert response.json == {"message": "Password changed"}
        assert can_login(client, EMAIL, new_password)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_change_password_nonexistent(auth_client: AuthenticatedClient) -> None:
    with auth_client as client:
        new_password = "new kids on the block"
        response = client.post(
            "/user/change-password", json={"email": EMAIL, "password": new_password}
        )
        assert response.status_code == 400
        assert response.json == {"message": "User doesn't exist"}


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_unauthorized(client: FlaskClient) -> None:
    """Check that we aren't able to access any of the end points if we don't have an
    authorization token.

    Note that this one, unlike all the others, uses the `client` rather than the
    `auth_client` fixture.
    """
    with client:
        assert_unauthorized(client, "get", "/user/list-users")
        assert_unauthorized(client, "post", "/user/create-user")
        assert_unauthorized(client, "delete", "/user/delete-user")
        assert_unauthorized(client, "post", "/user/change-password")
