"""
Test API endpoints for locations
"""
import json
import pytest
from unittest import mock

from dtbase.tests.conftest import check_for_docker
from dtbase.backend.api.location import routes

DOCKER_RUNNING = check_for_docker()


# use the testuser fixture to add a user to the database
@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_user(testuser):
    assert True


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_insert_location_schema(client):
    with client:
        schema = {
            "name": "building-floor-room",
            "description": "Find something within a building",
            "identifiers": [
                {"name": "building", "units": None, "datatype": "string"},
                {"name": "floor", "units": None, "datatype": "integer"},
                {"name": "room", "units": None, "datatype": "string"},
            ],
        }
        response = client.post(
            "/location/insert_location_schema", json=json.dumps(schema)
        )
        assert response.status_code == 201


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_insert_location_no_schema(client):
    with client:
        location = {
            "identifiers": [
                {"name": "x_distance", "units": "m", "datatype": "float"},
                {"name": "y_distance", "units": "m", "datatype": "float"},
                {"name": "z_distance", "units": "m", "datatype": "float"},
            ],
            "values": [5.0, 0.1, 4.4],
        }

        response = client.post("/location/insert_location", json=json.dumps(location))
        assert response.status_code == 201


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_insert_location_nonexisting_schema(client):
    with client:
        # use a non-existing schema name to insert a location
        with pytest.raises(ValueError):
            location = {"a": 123.4, "b": 432.1}
            response = client.post(
                "/location/insert_location/ab", json=json.dumps(location)
            )


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_insert_location_existing_schema(client):
    with client:
        schema = {
            "name": "xy",
            "description": "x-y coordinates in mm",
            "identifiers": [
                {"name": "x", "units": "mm", "datatype": "float"},
                {"name": "y", "units": "mm", "datatype": "float"},
            ],
        }
        response = client.post(
            "/location/insert_location_schema", json=json.dumps(schema)
        )
        assert response.status_code == 201

        # now use that schema to insert a location
        location = {"x": 123.4, "y": 432.1}
        response = client.post(
            "/location/insert_location/xy", json=json.dumps(location)
        )
        assert response.status_code == 201


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_list_locations_no_coords(client):
    with client:
        response = client.get("/location/list/xy")
        assert response.status_code == 200
        assert isinstance(response.json, list)
