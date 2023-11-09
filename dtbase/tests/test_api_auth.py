"""
Test API endpoints for authentication
"""
import pytest
from flask.testing import FlaskClient

from dtbase.tests.conftest import check_for_docker, get_token

DOCKER_RUNNING = check_for_docker()


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_get_token(client: FlaskClient, test_user):
    """Test getting an authetication token for the test user."""
    with client:
        response = get_token(client)
        assert response.status_code == 200
        body = response.json
        assert body is not None
        assert set(body.keys()) == {"access_token"}


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_get_token_nonexistent(client):
    """Test getting an authetication token for a non-existent test user."""
    with client:
        type_data = {
            "email": "snoopy@dogg.land",
            "password": "whatsmyname?",
        }
        response = client.post("/auth/new-token", json=type_data)
        assert response.status_code == 401
