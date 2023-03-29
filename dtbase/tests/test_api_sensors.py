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
def test_insert_sensor_readings(client):
    with client:
        # Insert a sensor type and a sensor
        response = insert_weather_type(client)
        assert response.status_code == 201
        sensor = {
            "unique_identifier": "THISISAUUIDISWEAR",
            "name": "Rooftop weather",
            "notes": "The blue weather sensor on the roof",
        }
        response = client.post("/sensor/insert_sensor/weather", json=json.dumps(sensor))
        assert response.status_code == 201

        # Test the insert_sensor_readings API endpoint
        sensor_readings = {
            "measure_name": "temperature",
            "sensor_uniq_id": "THISISAUUIDISWEAR",
            "readings": [290.5, 291.0, 291.5],
            "timestamps": [
                "2023-03-29T00:00:00",
                "2023-03-29T01:00:00",
                "2023-03-29T02:00:00",
            ],
        }
        response = client.post(
            "/sensor/insert_sensor_readings", json=json.dumps(sensor_readings)
        )
        assert response.status_code == 201


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_get_sensor_readings(client):
    with client:
        # Insert a sensor type and a sensor
        response = insert_weather_type(client)
        assert response.status_code == 201
        sensor = {
            "unique_identifier": "THISISAUUIDISWEAR",
            "name": "Rooftop weather",
            "notes": "The blue weather sensor on the roof",
        }
        response = client.post("/sensor/insert_sensor/weather", json=json.dumps(sensor))
        assert response.status_code == 201

        # Insert sensor readings
        sensor_readings = {
            "measure_name": "temperature",
            "sensor_uniq_id": "THISISAUUIDISWEAR",
            "readings": [290.5, 291.0, 291.5],
            "timestamps": [
                "2023-03-29T00:00:00",
                "2023-03-29T01:00:00",
                "2023-03-29T02:00:00",
            ],
        }
        response = client.post(
            "/sensor/insert_sensor_readings", json=json.dumps(sensor_readings)
        )
        assert response.status_code == 201

        # Test the get_sensor_readings API endpoint
        get_readings = {
            "measure_name": "temperature",
            "sensor_uniq_id": "THISISAUUIDISWEAR",
            "dt_from": "2023-03-29T00:00:00",
            "dt_to": "2023-03-29T02:00:00",
        }
        response = client.post("/sensor/sensor_readings", json=json.dumps(get_readings))
        assert response.status_code == 200
        assert len(response.json) == 3
        for reading in response.json:
            assert "value" in reading
            assert "timestamp" in reading


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_list_sensor_measures(client):
    with client:

        response = insert_weather_type(client)
        assert response.status_code == 201

        response = client.get("/sensor/list_measures")
        assert response.status_code == 200
        assert isinstance(response.json, list)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_list_sensor_types(client):
    with client:
        response = insert_weather_type(client)
        assert response.status_code == 201

        response = client.get("/sensor/list_sensor_types")
        assert response.status_code == 200
        assert isinstance(response.json, list)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_delete_sensor(client):
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

        response = client.delete("/sensor/delete_sensor/THISISAUUIDISWEAR")
        assert response.status_code == 200


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_delete_sensor_type(client):
    with client:
        response = insert_weather_type(client)
        assert response.status_code == 201
        response = client.delete("/sensor/delete_sensor_type/weather")
        assert response.status_code == 200
