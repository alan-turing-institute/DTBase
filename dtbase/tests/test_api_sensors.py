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
        
        
        
