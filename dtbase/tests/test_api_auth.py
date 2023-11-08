"""
Test API endpoints for authentication
"""
import pytest

from dtbase.tests.conftest import TEST_USER_EMAIL, TEST_USER_PASSWORD, check_for_docker

DOCKER_RUNNING = check_for_docker()


def get_token(client):
    """Get an authentication token for the test user."""
    type_data = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
    }
    response = client.post("/auth/new-token", json=type_data)
    return response


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_get_token(client, test_user):
    """Test getting an authetication token for the test user."""
    with client:
        response = get_token(client)
        assert response.status_code == 200
        body = response.json
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
