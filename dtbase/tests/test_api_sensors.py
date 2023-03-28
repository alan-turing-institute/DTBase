"""
Test API endpoints for sensors
"""
import json
import pytest
from unittest import mock

from dtbase.tests.conftest import check_for_docker
from dtbase.backend.api.sensor import routes

DOCKER_RUNNING = check_for_docker()


def insert_weather_type(client):
    type_data = {
        "name": "weather",
        "description": "Weather sensors that report both temperature and rain",
        "measures": [
            {"name": "temperature", "units": "Kelvin", "datatype": "float"},
            {"name": "is raining", "units": None, "datatype": "boolean"},
        ],
    }
    response = client.post("/sensor/insert_sensor_type", json=json.dumps(type_data))
    return response


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_insert_sensor_type(client):
    with client:
        response = insert_weather_type(client)
        assert response.status_code == 201


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_insert_sensor(client):
    with client:
        response = insert_weather_type(client)
        assert response.status_code == 201
        # Use that type to insert a sensor
        sensor = {
            "unique_identifier": "THISISAUUIDISWEAR",
            "name": "Rooftop weather",
            "notes": "The blue weather sensor on the roof",
        }
        response = client.post("/sensor/insert_sensor/weather", json=json.dumps(sensor))
        assert response.status_code == 201


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_list_sensors_of_a_type(client):
    with client:
        response = insert_weather_type(client)
        assert response.status_code == 201
        response = client.get("/sensor/list/weather")
        assert response.status_code == 200
        assert isinstance(response.json, list)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_sensor_locations(client):
    with client:
        # Insert a sensor type
        response = insert_weather_type(client)
        assert response.status_code == 201

        # Insert a sensor
        unique_id = "THISISAUUIDISWEAR"
        sensor = {
            "unique_identifier": unique_id,
            "name": "Rooftop weather",
            "notes": "The blue weather sensor on the roof",
        }
        response = client.post("/sensor/insert_sensor/weather", json=json.dumps(sensor))
        assert response.status_code == 201

        # Insert a location
        x_coord = 0.23
        y_coord = 1.44
        location = {
            "identifiers": [
                {"name": "x", "units": "centimetres", "datatype": "float"},
                {"name": "y", "units": "centimetres", "datatype": "float"},
            ],
            "values": [x_coord, y_coord],
        }
        response = client.post("/location/insert_location", json=json.dumps(location))
        assert response.status_code == 201
        schema_name = response.json["schema_name"]

        # Set the sensor location
        sensor_location = {
            "sensor_identifier": unique_id,
            "location_schema": schema_name,
            "coordinates": {"x": x_coord, "y": y_coord},
        }
        response = client.post(
            "/sensor/insert_sensor_location", json=json.dumps(sensor_location)
        )
        assert response.status_code == 201

        # Check that the sensor location has been set
        response = client.get(
            "/sensor/list_sensor_locations",
            json=json.dumps({"unique_identifier": unique_id}),
        )
        assert response.status_code == 200
        assert response.json[0]["x"] == x_coord
        assert response.json[0]["y"] == y_coord
