"""
Test API endpoints for users
"""
from collections.abc import Collection

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import Response
from starlette.routing import Route

from dtbase.core.constants import DEFAULT_USER_EMAIL

from .conftest import check_for_docker
from .utils import TEST_USER_EMAIL, assert_unauthorized, can_login

DOCKER_RUNNING = check_for_docker()


# Some example values used for testing.
EMAIL = "hubby@hobbob.bubbly"
PASSWORD = "iknowsecurity"


def create_user(client: TestClient) -> Response:
    """Create a user to test against."""
    type_data = {"email": EMAIL, "password": PASSWORD}
    response = client.post("/user/create-user", json=type_data)
    return response


def assert_list_users(client: TestClient, users: Collection[str]) -> None:
    """Assert that the `/user/list-users` end point returns successfully, and that it
    returns exactly the users provided in the second arguments.
    """
    response = client.get("/user/list-users")
    assert response.status_code == 200
    assert response.json() is not None
    assert set(response.json()) == set(users)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_create_user(auth_client: TestClient) -> None:
    response = create_user(auth_client)
    assert response.status_code == 201
    assert response.json() == {"detail": "User created"}
    assert_list_users(auth_client, {TEST_USER_EMAIL, DEFAULT_USER_EMAIL, EMAIL})
    assert can_login(auth_client, email=EMAIL, password=PASSWORD)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_create_user_duplicate(auth_client: TestClient) -> None:
    create_user(auth_client)
    response = create_user(auth_client)
    assert response.status_code == 409
    assert response.json() == {"detail": "User already exists"}


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_delete_user(auth_client: TestClient) -> None:
    create_user(auth_client)
    response = auth_client.post("/user/delete-user", json={"email": EMAIL})
    assert response.status_code == 200
    assert response.json() == {"detail": "User deleted"}
    assert_list_users(auth_client, {TEST_USER_EMAIL, DEFAULT_USER_EMAIL})


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_delete_user_nonexistent(auth_client: TestClient) -> None:
    response = auth_client.post("/user/delete-user", json={"email": EMAIL})
    assert response.status_code == 400
    assert response.json() == {"detail": "User doesn't exist"}


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_change_password(auth_client: TestClient) -> None:
    create_user(auth_client)
    new_password = "new kids on the block"
    response = auth_client.post(
        "/user/change-password", json={"email": EMAIL, "password": new_password}
    )
    assert response.status_code == 200
    assert response.json() == {"detail": "Password changed"}
    assert can_login(auth_client, EMAIL, new_password)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_change_password_nonexistent(auth_client: TestClient) -> None:
    new_password = "new kids on the block"
    response = auth_client.post(
        "/user/change-password", json={"email": EMAIL, "password": new_password}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "User doesn't exist"}


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_unauthorized(client: TestClient, app: FastAPI) -> None:
    """Check that we aren't able to access any of the end points if we don't have an
    authorization token.

    Note that this one, unlike all the others, uses the `client` rather than the
    `auth_client` fixture.
    """
    # loop through all endpoints
    for route in app.routes:
        if not isinstance(route, Route):
            # For some reason, FastAPI type-annotates app.routes as Sequence[BaseRoute],
            # rather than Sequence[Route]. In case we ever encounter a router isn't a
            # Route, raise an error.
            raise ValueError(f"route {route} is not a Route")
        methods = route.methods
        if methods is None:
            continue
        methods = iter(methods)
        if methods and route.path.startswith("/user"):
            method = next(methods)
            assert_unauthorized(client, method.lower(), route.path)
