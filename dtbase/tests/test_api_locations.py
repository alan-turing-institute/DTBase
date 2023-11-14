"""
Test API endpoints for locations
"""
from typing import Any

import pytest
from flask.testing import FlaskClient

from dtbase.tests.conftest import check_for_docker
from dtbase.tests.utils import assert_unauthorized

DOCKER_RUNNING = check_for_docker()


# use the test_user fixture to add a user to the database
@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_user(test_user: Any) -> None:
    assert True


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_insert_location_schema(auth_client: FlaskClient) -> None:
    with auth_client as client:
        schema = {
            "name": "building-floor-room",
            "description": "Find something within a building",
            "identifiers": [
                {"name": "building", "units": None, "datatype": "string"},
                {"name": "floor", "units": None, "datatype": "integer"},
                {"name": "room", "units": None, "datatype": "string"},
            ],
        }
        response = client.post("/location/insert-location-schema", json=schema)
        assert response.status_code == 201


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_insert_location_no_schema(auth_client: FlaskClient) -> None:
    with auth_client as client:
        location = {
            "identifiers": [
                {"name": "x_distance", "units": "m", "datatype": "float"},
                {"name": "y_distance", "units": "m", "datatype": "float"},
                {"name": "z_distance", "units": "m", "datatype": "float"},
            ],
            "values": [5.0, 0.1, 4.4],
        }

        response = client.post("/location/insert-location", json=location)
        assert response.status_code == 201


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_insert_location_nonexisting_schema(auth_client: FlaskClient) -> None:
    with auth_client as client:
        # use a non-existing schema name to insert a location
        with pytest.raises(ValueError):
            location = {"a": 123.4, "b": 432.1, "schema_name": "fakey"}
            client.post("/location/insert-location-for-schema", json=location)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_insert_location_existing_schema(auth_client: FlaskClient) -> None:
    with auth_client as client:
        schema = {
            "name": "xy",
            "description": "x-y coordinates in mm",
            "identifiers": [
                {"name": "x", "units": "mm", "datatype": "float"},
                {"name": "y", "units": "mm", "datatype": "float"},
            ],
        }
        response = client.post("/location/insert-location-schema", json=schema)
        assert response.status_code == 201

        # now use that schema to insert a location
        location = {"x": 123.4, "y": 432.1, "schema_name": "xy"}
        response = client.post("/location/insert-location-for-schema", json=location)
        assert response.status_code == 201


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_list_locations_no_coords(auth_client: FlaskClient) -> None:
    with auth_client as client:
        response = client.get("/location/list-locations", json={"schema_name": "xy"})
        assert response.status_code == 200
        assert isinstance(response.json, list)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_list_location_identifiers(auth_client: FlaskClient) -> None:
    with auth_client as client:
        # Insert location schemas with unique identifiers
        schema1 = {
            "name": "test-schema1",
            "description": "Test schema 1",
            "identifiers": [
                {"name": "test1", "units": None, "datatype": "string"},
                {"name": "test2", "units": None, "datatype": "integer"},
            ],
        }
        schema2 = {
            "name": "test-schema2",
            "description": "Test schema 2",
            "identifiers": [
                {"name": "test3", "units": None, "datatype": "string"},
                {"name": "test4", "units": None, "datatype": "integer"},
            ],
        }
        client.post("/location/insert-location-schema", json=schema1)
        client.post("/location/insert-location-schema", json=schema2)

        # Test list_location_identifiers
        response = client.get("/location/list-location-identifiers")
        assert response.status_code == 200

        # Check if the inserted identifiers are in the response
        identifier_names = [identifier["name"] for identifier in response.json]
        for identifier in schema1["identifiers"]:
            assert identifier["name"] in identifier_names

        for identifier in schema2["identifiers"]:
            assert identifier["name"] in identifier_names


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_list_location_schemas(auth_client: FlaskClient) -> None:
    with auth_client as client:
        # Insert location schemas
        schema1 = {
            "name": "test-schema1",
            "description": "Test schema 1",
            "identifiers": [
                {"name": "test1", "units": None, "datatype": "string"},
                {"name": "test2", "units": None, "datatype": "integer"},
            ],
        }
        schema2 = {
            "name": "test-schema2",
            "description": "Test schema 2",
            "identifiers": [
                {"name": "test3", "units": None, "datatype": "string"},
                {"name": "test4", "units": None, "datatype": "integer"},
            ],
        }
        client.post("/location/insert-location-schema", json=schema1)
        client.post("/location/insert-location-schema", json=schema2)

        # Test list_location_schemas
        response = client.get("/location/list-location-schemas")
        assert response.status_code == 200

        # Check if the inserted schemas are in the response
        schema_names = [schema["name"] for schema in response.json]
        assert schema1["name"] in schema_names
        assert schema2["name"] in schema_names


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_delete_location_schema(auth_client: FlaskClient) -> None:
    with auth_client as client:
        # First, insert a location schema to delete later
        schema = {
            "name": "test-schema",
            "description": "A test schema for deletion",
            "identifiers": [
                {"name": "test1", "units": None, "datatype": "string"},
                {"name": "test2", "units": None, "datatype": "integer"},
            ],
        }
        response = client.post("/location/insert-location-schema", json=schema)
        assert response.status_code == 201

        # Check if the schema was inserted successfully
        response = client.get("/location/list-location-schemas")
        schemas = response.get_json()
        assert any(s["name"] == "test-schema" for s in schemas)

        # Delete the location schema
        response = client.delete(
            "/location/delete-location-schema", json={"schema_name": "test-schema"}
        )
        assert response.status_code == 200

        # Check if the schema was deleted successfully
        response = client.get("/location/list-location-schemas")
        schemas = response.get_json()
        assert not any(s["name"] == "test-schema" for s in schemas)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_delete_location(auth_client: FlaskClient) -> None:
    with auth_client as client:
        # Insert a location schema and a location
        schema = {
            "name": "test-schema",
            "description": "Test schema for deletion",
            "identifiers": [
                {"name": "x", "units": "m", "datatype": "float"},
                {"name": "y", "units": "m", "datatype": "float"},
            ],
        }
        client.post("/location/insert-location-schema", json=schema)

        location = {"x": 1.0, "y": 2.0, "schema_name": "test-schema"}
        client.post("/location/insert-location-for-schema", json=location)

        # Test delete_location
        response = client.delete(
            "/location/delete-location",
            json=location,
        )
        assert response.status_code == 200

        # # Check if the location was deleted
        response = client.get("/location/list-locations", json=location)
        assert response.status_code == 200
        assert len(response.json) == 0


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_unauthorized(client):
    """Check that we aren't able to access any of the end points if we don't have an
    authorization token.

    Note that this one, unlike all the others, uses the `client` rather than the
    `auth_client` fixture.
    """
    with client:
        assert_unauthorized(client, "post", "/location/insert-location-schema")
        assert_unauthorized(client, "post", "/location/insert-location")
        assert_unauthorized(client, "post", "/location/insert-location-for-schema")
        assert_unauthorized(client, "get", "/location/list-locations")
        assert_unauthorized(client, "get", "/location/list-location-identifiers")
        assert_unauthorized(client, "get", "/location/list-location-schemas")
        assert_unauthorized(client, "delete", "/location/delete-location")
        assert_unauthorized(client, "delete", "/location/delete-location-schema")
