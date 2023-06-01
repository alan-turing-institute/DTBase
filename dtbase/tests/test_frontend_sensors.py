"""
Test that the DTBase sensors pages load
"""
from flask import url_for, request
import pytest
import requests_mock

MOCK_SENSOR_TYPES = [
    {
        "name": "sensorType1",
        "measures": [
            {"name": "Temperature", "units": "degrees C", "datatype": "float"},
            {"name": "Humidity", "units": "percent", "datatype": "float"},
        ],
    }
]

MOCK_SENSORS = [
    {
        "id": 1,
        "name": "aSensor",
        "sensor_type_name": "sensorType1",
        "unique_identifier": "sensor1",
    },
]

MOCK_SENSOR_READINGS = [
    {"timestamp": "2023-01-01T00:00:00", "value": 23.4},
    {"timestamp": "2023-01-01T00:10:00", "value": 24.5},
    {"timestamp": "2023-01-01T00:20:00", "value": 25.6},
    {"timestamp": "2023-01-01T00:30:00", "value": 26.7},
    {"timestamp": "2023-01-01T00:40:00", "value": 27.8},
]


def test_sensors_timeseries_no_backend(frontend_client):
    with frontend_client:
        response = frontend_client.get(
            "/sensors/time-series-plots", follow_redirects=True
        )
        assert response.status_code == 200
        html_content = response.data.decode("utf-8")
        assert "Backend API not found" in html_content


def test_sensors_timeseries_no_sensor_types(frontend_client):
    with frontend_client:
        with requests_mock.Mocker() as m:
            m.get("http://localhost:5000/sensor/list_sensor_types", json=[])
            response = frontend_client.get("/sensors/time-series-plots")
            assert response.status_code == 200
            html_content = response.data.decode("utf-8")
            assert "Choose sensors and time period" in html_content


def test_sensors_timeseries_dummy_sensor_types(frontend_client):
    with frontend_client:
        with requests_mock.Mocker() as m:
            m.get(
                "http://localhost:5000/sensor/list_sensor_types",
                json=[{"name": "dummyType1"}, {"name": "dummyType2"}],
            )
            # also mock the responses to getting the sensors of each type
            m.get("http://localhost:5000/sensor/list/dummyType1", json=[])
            m.get("http://localhost:5000/sensor/list/dummyType2", json=[])
            response = frontend_client.get("/sensors/time-series-plots")
            assert response.status_code == 200
            html_content = response.data.decode("utf-8")
            assert 'value="dummyType1"' in html_content
            assert 'value="dummyType2"' in html_content


def test_sensors_timeseries_no_sensor_data(frontend_client):
    with frontend_client:
        with requests_mock.Mocker() as m:
            m.get(
                "http://localhost:5000/sensor/list_sensor_types",
                json=[{"name": "sensorType1"}],
            )
            # also mock the responses to getting the sensors of each type
            m.get("http://localhost:5000/sensor/list/sensorType1", json=MOCK_SENSORS)
            response = frontend_client.get("/sensors/time-series-plots")
            assert response.status_code == 200
            html_content = response.data.decode("utf-8")
            assert 'value="sensor1"' in html_content


def test_sensors_timeseries_with_data(frontend_client):
    with frontend_client:
        with requests_mock.Mocker() as m:
            m.get(
                "http://localhost:5000/sensor/list_sensor_types", json=MOCK_SENSOR_TYPES
            )
            # also mock the responses to getting the sensors of each type
            m.get("http://localhost:5000/sensor/list/sensorType1", json=MOCK_SENSORS)
            m.get(
                "http://localhost:5000/sensor/sensor_readings",
                json=MOCK_SENSOR_READINGS,
            )
            # URL will now include startDate, endDate, sensorIds etc
            response = frontend_client.get(
                "/sensors/time-series-plots?startDate=2023-01-01&endDate=2023-02-01&sensorIds=sensor1&sensorType=sensorType1"
            )
            assert response.status_code == 200
            html_content = response.data.decode("utf-8")
            # check that it draws canvases for the plots
            assert '<canvas id="TemperatureCanvas"></canvas>' in html_content
            assert '<canvas id="HumidityCanvas"></canvas>' in html_content


def test_sensors_readings_no_backend(frontend_client):
    with frontend_client:
        response = frontend_client.get("/sensors/readings", follow_redirects=True)
        assert response.status_code == 200
        html_content = response.data.decode("utf-8")
        assert "Backend API not found" in html_content


def test_sensors_readings_initial_get(frontend_client):
    with frontend_client:
        with requests_mock.Mocker() as m:
            m.get("http://localhost:5000/sensor/list_sensor_types", json=[])
            response = frontend_client.get("/sensors/readings")
            assert response.status_code == 200
            html_content = response.data.decode("utf-8")
            assert "Time period" in html_content


def test_sensors_readings_post_time_period(frontend_client):
    with frontend_client:
        with requests_mock.Mocker() as m:
            m.get("http://localhost:5000/sensor/list_sensor_types", json=[])
            response = frontend_client.post(
                "/sensors/readings",
                data={"startDate": "2023-01-01", "endDate": "2023-02-01"},
            )
            assert response.status_code == 200
            html_content = response.data.decode("utf-8")
            assert "Sensor Type" in html_content


def test_sensors_readings_post_sensor(frontend_client):
    with frontend_client:
        with requests_mock.Mocker() as m:
            m.get(
                "http://localhost:5000/sensor/list_sensor_types", json=MOCK_SENSOR_TYPES
            )
            m.get("http://localhost:5000/sensor/list/sensorType1", json=MOCK_SENSORS)
            m.get(
                "http://localhost:5000/sensor/sensor_readings",
                json=MOCK_SENSOR_READINGS,
            )
            response = frontend_client.post(
                "/sensors/readings",
                data={
                    "startDate": "2023-01-01",
                    "endDate": "2023-02-01",
                    "sensor_type": "sensorType1",
                    "sensor": "sensor1",
                },
            )
            assert response.status_code == 200
            html_content = response.data.decode("utf-8")
            assert "Uploaded sensorType1 Sensor Data for sensor1" in html_content
            # column headings for Timestamp and each measure
            assert "<th>Timestamp</th>" in html_content
            assert "<th>Temperature</th>" in html_content
            assert "<th>Humidity</th>" in html_content
            # 5 rows of data plus the header row
            assert html_content.count("<tr>") == 6
