"""
Test that the DTBase models pages load
"""
import requests_mock
from flask.testing import FlaskClient

MOCK_PREDICTION_DATA = {
    "temperatureMean": [
        {"value": 18.8, "timestamp": "2023-01-01T00:00:00"},
        {"value": 18.9, "timestamp": "2023-01-01T00:02:00"},
        {"value": 18.7, "timestamp": "2023-01-01T00:04:00"},
    ],
    "temperatureUpper Bound": [
        {"value": 25.8, "timestamp": "2023-01-01T00:00:00"},
        {"value": 27.3, "timestamp": "2023-01-01T00:02:00"},
        {"value": 27.7, "timestamp": "2023-01-01T00:04:00"},
    ],
    "temperatureLower Bound": [
        {"value": 15.8, "timestamp": "2023-01-01T00:00:00"},
        {"value": 17.3, "timestamp": "2023-01-01T00:02:00"},
        {"value": 17.7, "timestamp": "2023-01-01T00:04:00"},
    ],
}

MOCK_SENSOR_DATA = {
    "sensor_uniq_id": "TRH1",
    "measure_name": "temperature",
    "readings": [
        (18.82, "2023-01-01T00:00:00"),
        (18.92, "2023-01-01T00:02:00"),
    ],
}

MOCK_RUN_SENSOR_MEASURE_DATA = {
    "sensor_unique_id": "TRH1",
    "sensor_measure": {"name": "temperature", "units": "degrees Celsius"},
}


def test_models_index_backend(auth_frontend_client: FlaskClient) -> None:
    with auth_frontend_client as client:
        response = client.get("/models/index", follow_redirects=True)
        assert response.status_code == 200
        html_content = response.data.decode("utf-8")
        assert "Filter modelling results" in html_content


def test_models_index_no_models_mock(mock_auth_frontend_client: FlaskClient) -> None:
    with mock_auth_frontend_client as client:
        with requests_mock.Mocker() as m:
            m.get("http://localhost:5000/model/list-models", json=[])
            m.get(
                "http://localhost:5000/model/list-model-scenarios",
                json=[],
            )
            response = client.get("/models/index")
            assert response.status_code == 200
            html_content = response.data.decode("utf-8")
            assert "Filter modelling results" in html_content


def test_models_index_no_runs_mock(mock_auth_frontend_client: FlaskClient) -> None:
    with mock_auth_frontend_client as client:
        with requests_mock.Mocker() as m:
            m.get(
                "http://localhost:5000/model/list-models",
                json=[{"name": "model1"}, {"name": "model2"}],
            )
            m.get(
                "http://localhost:5000/model/list-model-scenarios",
                json=[
                    {"description": "Scenario 1", "model_name": "model1"},
                    {"description": "Scenario 2", "model_name": "model2"},
                ],
            )
            m.get("http://localhost:5000/model/list-model-runs", json=[])
            response = client.get("/models/index")
            assert response.status_code == 200
            html_content = response.data.decode("utf-8")
            # should have a select block including model1 and model2
            assert 'value="model1"' in html_content
            assert 'value="model2"' in html_content
            # now select model2
            response = client.post("/models/index", data={"model_name": "model2"})
            assert response.status_code == 200
            html_content = response.data.decode("utf-8")
            assert "Predictive model:" in html_content


def test_models_index_with_data_mock(mock_auth_frontend_client: FlaskClient) -> None:
    with mock_auth_frontend_client as client:
        with requests_mock.Mocker() as m:
            m.get(
                "http://localhost:5000/model/list-models",
                json=[{"name": "model1"}, {"name": "model2"}],
            )
            m.get(
                "http://localhost:5000/model/list-model-scenarios",
                json=[
                    {"description": "Scenario 1", "model_name": "model1"},
                    {"description": "Scenario 2", "model_name": "model2"},
                ],
            )
            m.get("http://localhost:5000/model/list-model-runs", json=[1, 2])
            m.get(
                "http://localhost:5000/model/get-model-run", json=MOCK_PREDICTION_DATA
            )
            m.get(
                "http://localhost:5000/model/get-model-run-sensor-measure",
                json=MOCK_RUN_SENSOR_MEASURE_DATA,
            )
            m.get("http://localhost:5000/sensor/sensor-readings", json=MOCK_SENSOR_DATA)
            response = client.get("/models/index")
            # select model1 and run_id 2
            response = client.post(
                "/models/index", data={"model_name": "model2", "run_id": 2}
            )
            assert response.status_code == 200
            html_content = response.data.decode("utf-8")
            assert "Model predictions" in html_content
            # should be a canvas containing a plot
            assert '<canvas id="model_plot">' in html_content
