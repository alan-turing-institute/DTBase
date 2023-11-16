"""
Test API endpoints for authentication
"""
import time

import pytest
from flask import Flask
from flask.testing import FlaskClient

from dtbase.tests.conftest import check_for_docker
from dtbase.tests.utils import can_login, get_token

DOCKER_RUNNING = check_for_docker()


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_get_token(client: FlaskClient, test_user: None) -> None:
    """Test getting an authetication token for the test user."""
    with client:
        assert can_login(client)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_get_token_nonexistent(client: FlaskClient) -> None:
    """Test getting an authetication token for a non-existent test user."""
    with client:
        response = get_token(client, email="snoopy@dogg.land", password="whatsmyname?")
        assert response.status_code == 401


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_refresh_token(client: FlaskClient, test_user: None) -> None:
    """Test refreshing an authentication token."""
    with client:
        response1 = get_token(client)
        body1 = response1.json
        assert response1.status_code == 200 and body1 is not None
        refresh_token = body1["refresh_token"]

        response2 = client.post(
            "/auth/refresh", headers={"Authorization": f"Bearer {refresh_token}"}
        )
        body2 = response2.json
        assert response2.status_code == 200 and body2 is not None
        assert set(body2.keys()) == {"access_token", "refresh_token"}


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_refresh_token_expired(app: Flask, test_user: None) -> None:
    """Test refreshing an authentication token when the refresh token has expired."""
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = 1
    with app.test_client() as client:
        response1 = get_token(client)
        body1 = response1.json
        assert response1.status_code == 200 and body1 is not None
        refresh_token = body1["refresh_token"]
        time.sleep(1)  # By the time this is done, the token should have expired.

        response2 = client.post(
            "/auth/refresh", headers={"Authorization": f"Bearer {refresh_token}"}
        )
        assert response2.status_code == 401
        assert response2.json == {"msg": "Token has expired"}
