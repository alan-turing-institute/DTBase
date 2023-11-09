"""
Test API endpoints for sensors
"""
import pytest

from dtbase.tests.conftest import check_for_docker
from dtbase.tests.utils import assert_unauthorized

DOCKER_RUNNING = check_for_docker()


UNIQ_ID1 = "THISISAUUIDISWEAR"
X_COORD = 0.23
Y_COORD = 1.44


def insert_weather_type(client):
    type_data = {
        "name": "weather",
        "description": "Weather sensors that report both temperature and rain",
        "measures": [
            {"name": "temperature", "units": "Kelvin", "datatype": "float"},
            {"name": "is raining", "units": None, "datatype": "boolean"},
        ],
    }
    response = client.post("/sensor/insert-sensor-type", json=type_data)
    return response


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_insert_sensor_type(auth_client):
    with auth_client as client:
        response = insert_weather_type(client)
        assert response.status_code == 201


def insert_weather_sensor(client):
    # Use that type to insert a sensor
    sensor = {
        "unique_identifier": UNIQ_ID1,
        "type_name": "weather",
        "name": "Rooftop weather",
        "notes": "The blue weather sensor on the roof",
    }
    response = client.post("/sensor/insert-sensor", json=sensor)
    return response


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_insert_sensor(auth_client):
    with auth_client as client:
        response = insert_weather_type(client)
        assert response.status_code == 201
        # Use that type to insert a sensor
        response = insert_weather_sensor(client)
        assert response.status_code == 201


def insert_temperature_sensor(client):
    # insert a temperature sensor
    type_data = {
        "name": "simpletemp",
        "description": "Simple temperature sensor",
        "measures": [
            {"name": "temperature", "units": "Kelvin", "datatype": "float"},
        ],
    }
    response = client.post("/sensor/insert-sensor-type", json=type_data)
    return response


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_insert_two_sensor_types_sharing_measure(auth_client):
    with auth_client as client:
        response = insert_weather_type(client)
        assert response.status_code == 201
        response = insert_temperature_sensor(client)
        assert response.status_code == 201
        response = client.get("/sensor/list-sensor-types")
        stypes = response.json
        assert len(stypes) == 2
        weather = next(t for t in stypes if t["name"] == "weather")
        assert isinstance(weather, dict)
        assert len(weather["measures"]) == 2
        temp = next(t for t in stypes if t["name"] == "simpletemp")
        assert isinstance(temp, dict)
        assert len(temp["measures"]) == 1


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_list_sensors_of_a_type(auth_client):
    with auth_client as client:
        response = insert_weather_type(client)
        assert response.status_code == 201
        response = client.get("/sensor/list-sensors", json={"type_name": "weather"})
        assert response.status_code == 200
        assert isinstance(response.json, list)


def insert_sensor_location(client):
    # Insert a sensor
    insert_weather_type(client)
    insert_weather_sensor(client)

    # Insert a location
    location = {
        "identifiers": [
            {"name": "x", "units": "centimetres", "datatype": "float"},
            {"name": "y", "units": "centimetres", "datatype": "float"},
        ],
        "values": [X_COORD, Y_COORD],
    }
    response = client.post("/location/insert-location", json=location)
    location_schema = response.json["schema_name"]

    # Set the sensor location
    sensor_location = {
        "unique_identifier": UNIQ_ID1,
        "schema_name": location_schema,
        "coordinates": {"x": X_COORD, "y": Y_COORD},
    }
    response = client.post("/sensor/insert-sensor-location", json=sensor_location)
    return response


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_insert_sensor_locations(auth_client):
    with auth_client as client:
        response = insert_sensor_location(client)
        assert response.status_code == 201


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_get_sensor_locations(auth_client):
    with auth_client as client:
        response = insert_sensor_location(client)
        # Check that the sensor location has been set
        response = client.get(
            "/sensor/list-sensor-locations",
            json={"unique_identifier": UNIQ_ID1},
        )
        assert response.status_code == 200
        assert response.json[0]["x"] == X_COORD
        assert response.json[0]["y"] == Y_COORD


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_insert_sensor_readings(auth_client):
    with auth_client as client:
        # Insert a sensor type and a sensor
        response = insert_weather_type(client)
        assert response.status_code == 201
        response = insert_weather_sensor(client)
        assert response.status_code == 201

        # Test the insert_sensor_readings API endpoint
        sensor_readings = {
            "measure_name": "temperature",
            "unique_identifier": UNIQ_ID1,
            "readings": [290.5, 291.0, 291.5],
            "timestamps": [
                "2023-03-29T00:00:00",
                "2023-03-29T01:00:00",
                "2023-03-29T02:00:00",
            ],
        }
        response = client.post("/sensor/insert-sensor-readings", json=sensor_readings)
        assert response.status_code == 201


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_get_sensor_readings(auth_client):
    with auth_client as client:
        # Insert a sensor type and a sensor
        response = insert_weather_type(client)
        assert response.status_code == 201
        response = insert_weather_sensor(client)
        assert response.status_code == 201

        # Insert sensor readings
        sensor_readings = {
            "measure_name": "temperature",
            "unique_identifier": UNIQ_ID1,
            "readings": [290.5, 291.0, 291.5],
            "timestamps": [
                "2023-03-29T00:00:00",
                "2023-03-29T01:00:00",
                "2023-03-29T02:00:00",
            ],
        }
        response = client.post("/sensor/insert-sensor-readings", json=sensor_readings)
        assert response.status_code == 201

        # Test the get_sensor_readings API endpoint
        get_readings = {
            "measure_name": "temperature",
            "unique_identifier": UNIQ_ID1,
            "dt_from": "2023-03-29T00:00:00",
            "dt_to": "2023-03-29T02:00:00",
        }
        response = client.get("/sensor/sensor-readings", json=get_readings)
        assert response.status_code == 200
        assert len(response.json) == 3
        for reading in response.json:
            assert "value" in reading
            assert "timestamp" in reading


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_list_sensor_measures(auth_client):
    with auth_client as client:
        response = insert_weather_type(client)
        assert response.status_code == 201

        response = client.get("/sensor/list-measures")
        assert response.status_code == 200
        assert isinstance(response.json, list)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_list_sensor_types(auth_client):
    with auth_client as client:
        response = insert_weather_type(client)
        assert response.status_code == 201

        response = client.get("/sensor/list-sensor-types")
        assert response.status_code == 200
        assert isinstance(response.json, list)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_delete_sensor(auth_client):
    with auth_client as client:
        response = insert_weather_type(client)
        assert response.status_code == 201
        # Use that type to insert a sensor
        response = insert_weather_sensor(client)
        assert response.status_code == 201

        response = client.delete(
            "/sensor/delete-sensor", json={"unique_identifier": UNIQ_ID1}
        )
        assert response.status_code == 200


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_delete_sensor_type(auth_client):
    with auth_client as client:
        response = insert_weather_type(client)
        assert response.status_code == 201
        response = client.delete(
            "/sensor/delete-sensor-type", json={"type_name": "weather"}
        )
        assert response.status_code == 200


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_unauthorized(client):
    """Check that we aren't able to access any of the end points if we don't have an
    authorization token.

    Note that this one, unlike all the others, uses the `client` rather than the
    `auth_client` fixture.
    """
    with client:
        assert_unauthorized(client, "post", "/sensor/insert-sensor-type")
        assert_unauthorized(client, "post", "/sensor/insert-sensor")
        assert_unauthorized(client, "post", "/sensor/insert-sensor-location")
        assert_unauthorized(client, "post", "/sensor/insert-sensor-readings")
        assert_unauthorized(client, "get", "/sensor/list-sensor-types")
        assert_unauthorized(client, "get", "/sensor/list-sensors")
        assert_unauthorized(client, "get", "/sensor/list-measures")
        assert_unauthorized(client, "get", "/sensor/list-sensor-locations")
        assert_unauthorized(client, "get", "/sensor/sensor-readings")
        assert_unauthorized(client, "delete", "/sensor/delete-sensor-type")
        assert_unauthorized(client, "delete", "/sensor/delete-sensor")
