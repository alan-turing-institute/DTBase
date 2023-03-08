"""
Test API endpoints
"""
import json
import pytest

from dtbase.tests.conftest import check_for_docker

DOCKER_RUNNING = check_for_docker()


# use the testuser fixture to add a user to the database
@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_user(testuser):
    assert True


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_insert_location(client):
    with client:
        location = {
            "identifiers": [
                {"name": "x_distance", "units": "m", "datatype": "float"},
                {"name": "y_distance", "units": "m", "datatype": "float"},
                {"name": "z_distance", "units": "m", "datatype": "float"},
            ],
            "values": [5.0, 0.1, 4.4]
        }

        response = client.post("/location/insert_location", json=json.dumps(location))
        assert response.status_code == 200
