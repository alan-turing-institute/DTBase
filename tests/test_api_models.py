"""
Test API endpoints for models
"""
import datetime as dt

import pytest
from dateutil.parser import parse
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import Response
from starlette.routing import Route

from .conftest import check_for_docker
from .test_api_sensors import UNIQ_ID1 as SENSOR_ID1
from .test_api_sensors import insert_weather_sensor, insert_weather_type
from .utils import assert_unauthorized

DOCKER_RUNNING = check_for_docker()


# Some example data we'll use in many of the tests.

NOW = dt.datetime.now(dt.timezone.utc)

MODEL_NAME1 = "Murphy's Law"
MODEL_NAME2 = "My Fortune Teller Says So"

SCENARIO1 = "The absolute worst case scenario"
SCENARIO2 = "The really-bad-but-could-actually-technically-be-worse scenario"
SCENARIO3 = "Use only a single deck of tarot cards."

MEASURE_NAME1 = "mean temperature"
MEASURE_UNITS1 = "Kelvin"
MEASURE_NAME2 = "likely to rain"
MEASURE_UNITS2 = ""
MEASURE1 = {
    "name": MEASURE_NAME1,
    "units": MEASURE_UNITS1,
    "datatype": "float",
}
MEASURE2 = {
    "name": MEASURE_NAME2,
    "units": MEASURE_UNITS2,
    "datatype": "boolean",
}

TIMESTAMPS1 = [
    x.isoformat()
    for x in [
        NOW + dt.timedelta(days=1),
        NOW + dt.timedelta(days=2),
        NOW + dt.timedelta(days=3),
    ]
]
TIMESTAMPS2 = [
    x.isoformat()
    for x in [
        NOW + dt.timedelta(weeks=1),
        NOW + dt.timedelta(weeks=2),
        NOW + dt.timedelta(weeks=3),
    ]
]
PRODUCT1 = {
    "measure_name": MEASURE_NAME1,
    "values": [-23.0, -23.0, -23.1],
    "timestamps": TIMESTAMPS1,
}
PRODUCT2 = {
    "measure_name": MEASURE_NAME2,
    "values": [True, True, True],
    "timestamps": TIMESTAMPS1,
}
PRODUCT3 = {
    "measure_name": MEASURE_NAME2,
    "values": [False, True, False],
    "timestamps": TIMESTAMPS2,
}
RUN1 = {
    "model_name": MODEL_NAME1,
    "scenario_description": SCENARIO1,
    "measures_and_values": [PRODUCT1],
}
RUN2 = {
    "model_name": MODEL_NAME1,
    "scenario_description": SCENARIO2,
    "measures_and_values": [PRODUCT1, PRODUCT2],
    "time_created": (NOW - dt.timedelta(days=7)).isoformat(),
    "sensor_unique_id": SENSOR_ID1,
    "sensor_measure": {
        "name": "temperature",
        "units": "Kelvin",
    },
}
RUN3 = {
    "model_name": MODEL_NAME2,
    "scenario_description": SCENARIO3,
    "measures_and_values": [PRODUCT3],
    "create_scenario": True,
}


def insert_model(client: TestClient, name: str) -> None:
    response = client.post("/model/insert-model", json={"name": name})
    assert response.status_code == 201


def insert_model_measures(client: TestClient) -> tuple[Response, Response]:
    response1 = client.post("/model/insert-model-measure", json=MEASURE1)
    response2 = client.post("/model/insert-model-measure", json=MEASURE2)
    return response1, response2


def insert_model_scenarios(client: TestClient) -> list[Response]:
    insert_model(client, MODEL_NAME1)
    insert_model(client, MODEL_NAME2)
    responses = [
        client.post(
            "/model/insert-model-scenario",
            json={"model_name": model_name, "description": scenario},
        )
        for model_name, scenario in (
            (MODEL_NAME1, SCENARIO1),
            (MODEL_NAME1, SCENARIO2),
            (MODEL_NAME2, SCENARIO3),
        )
    ]
    return responses


def insert_model_runs(
    client: TestClient,
) -> tuple[Response, Response, Response]:
    insert_model_measures(client)
    insert_model_scenarios(client)
    insert_weather_type(client)
    insert_weather_sensor(client)
    response1 = client.post("/model/insert-model-run", json=RUN1)
    response2 = client.post("/model/insert-model-run", json=RUN2)
    response3 = client.post("/model/insert-model-run", json=RUN3)
    return response1, response2, response3


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_insert_model(auth_client: TestClient) -> None:
    model = {"name": MODEL_NAME1}
    response = auth_client.post("/model/insert-model", json=model)
    assert response.status_code == 201


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_list_models(auth_client: TestClient) -> None:
    # add two models
    insert_model(auth_client, MODEL_NAME1)
    insert_model(auth_client, MODEL_NAME2)

    # list models
    response = auth_client.get("/model/list-models")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 2


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_delete_model(auth_client: TestClient) -> None:
    # add a model
    insert_model(auth_client, MODEL_NAME1)

    # delete model
    response = auth_client.post("/model/delete-model", json={"name": MODEL_NAME1})
    assert response.status_code == 200

    # check that model was deleted
    response = auth_client.get("/model/list-models")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 0


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_insert_model_scenario(auth_client: TestClient) -> None:
    # add a model scenario
    responses = insert_model_scenarios(auth_client)
    for response in responses:
        assert response.status_code == 201


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_insert_model_scenario_duplicate(auth_client: TestClient) -> None:
    insert_model_scenarios(auth_client)
    response = auth_client.post(
        "/model/insert-model-scenario",
        json={"model_name": MODEL_NAME1, "description": SCENARIO1},
    )
    assert response.status_code == 409


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_list_model_scenarios(auth_client: TestClient) -> None:
    # add a model scenario
    insert_model_scenarios(auth_client)
    # list model scenarios
    response = auth_client.get("/model/list-model-scenarios")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 3


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_delete_model_scenario(auth_client: TestClient) -> None:
    # add a model scenario
    insert_model_scenarios(auth_client)
    # delete model scenario
    response = auth_client.post(
        "/model/delete-model-scenario",
        json={"model_name": MODEL_NAME1, "description": SCENARIO1},
    )
    assert response.status_code == 200

    # check that model scenario was deleted
    response = auth_client.get("/model/list-model-scenarios")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 2


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_insert_model_measures(auth_client: TestClient) -> None:
    responses = insert_model_measures(auth_client)
    assert responses is not None
    for response in responses:
        assert response.status_code == 201


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_list_model_measures(auth_client: TestClient) -> None:
    insert_model_measures(auth_client)
    response = auth_client.get("/model/list-model-measures")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data is not None
    assert len(response_data) == 2
    expected_keys = {"name", "units", "datatype"}
    assert set(response_data[0].keys()) == expected_keys
    assert set(response_data[1].keys()) == expected_keys
    for k, v in MEASURE1.items():
        assert response_data[0][k] == v
    for k, v in MEASURE2.items():
        assert response_data[1][k] == v


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_delete_model_measures(auth_client: TestClient) -> None:
    insert_model_measures(auth_client)
    response = auth_client.post(
        "/model/delete-model-measure",
        json={"name": MEASURE_NAME1},
    )
    assert response.status_code == 200
    response = auth_client.get("/model/list-model-measures")
    response_data = response.json()
    assert response_data is not None
    assert len(response_data) == 1


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_insert_model_runs(auth_client: TestClient) -> None:
    responses = insert_model_runs(auth_client)
    assert responses is not None
    for response in responses:
        assert response.status_code == 201


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_list_model_runs(auth_client: TestClient) -> None:
    insert_model_runs(auth_client)

    payload = {
        "model_name": MODEL_NAME1,
        "dt_from": NOW.isoformat(),
        "dt_to": (NOW + dt.timedelta(days=10)).isoformat(),
        "scenario": SCENARIO1,
    }
    response = auth_client.post("/model/list-model-runs", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body is not None
    assert len(body) == 1

    expected_keys = {
        "id",
        "model_id",
        "model_name",
        "scenario_id",
        "scenario_description",
        "time_created",
        "sensor_unique_id",
        "sensor_measure",
    }
    run = body[0]
    assert set(run.keys()) == expected_keys
    for k in ("model_name", "scenario_description"):
        assert run[k] == RUN1[k]
    for k in ("sensor_measure", "sensor_unique_id"):
        assert run[k] is None

    payload = {
        "model_name": MODEL_NAME1,
        "dt_from": (NOW - dt.timedelta(days=10)).isoformat(),
        "dt_to": (NOW + dt.timedelta(days=10)).isoformat(),
    }
    response = auth_client.post("/model/list-model-runs", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body is not None
    assert len(body) == 2
    for run in body:
        if "time_created" in run:
            # The conversion to and from isoformat is because of ambiguity in having a
            # trailing Z vs +00:00.
            run["time_created"] = parse(run["time_created"]).isoformat()
        assert set(run.keys()) == expected_keys
        expected_run = RUN1 if run["id"] == 1 else RUN2
        for k in expected_keys:
            if k in expected_run:
                expected_value = expected_run[k]
                assert run[k] == expected_value


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_get_model_run(auth_client: TestClient) -> None:
    insert_model_runs(auth_client)

    runs = {
        "model_name": MODEL_NAME1,
        "dt_from": NOW.isoformat(),
        "dt_to": (NOW + dt.timedelta(days=10)).isoformat(),
        "scenario": SCENARIO1,
    }
    response = auth_client.post("/model/list-model-runs", json=runs)
    assert response.json() is not None
    run_id = response.json()[0]["id"]

    response = auth_client.post("/model/get-model-run", json={"run_id": run_id})
    assert response.status_code == 200
    body = response.json()
    assert body is not None
    assert len(body.keys()) == 1
    key, value = next(iter(body.items()))
    for v in value:
        if "timestamp" in v:
            # The conversion to and from isoformat is because of ambiguity in having a
            # trailing Z vs +00:00.
            v["timestamp"] = parse(v["timestamp"]).isoformat()
    assert key in {MEASURE_NAME1, MEASURE_NAME2}
    if key == MEASURE_NAME1:
        expected_product = PRODUCT1
    else:
        expected_product = PRODUCT2
    assert value == [
        {"timestamp": t, "value": v}
        for t, v in zip(expected_product["timestamps"], expected_product["values"])
    ]


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_get_model_run_sensor_measure(auth_client: TestClient) -> None:
    insert_model_runs(auth_client)

    runs = {
        "model_name": MODEL_NAME1,
        "dt_from": (NOW - dt.timedelta(days=10)).isoformat(),
        "dt_to": (NOW + dt.timedelta(days=10)).isoformat(),
    }
    response = auth_client.post("/model/list-model-runs", json=runs)
    assert response.status_code == 200
    assert response.json() is not None
    assert len(response.json()) == 2

    for run in response.json():
        run_id = run["id"]
        response = auth_client.post(
            "/model/get-model-run-sensor-measure", json={"run_id": run_id}
        )
        assert response.status_code == 200
        body = response.json()
        assert body is not None
        assert set(body.keys()) == {"sensor_unique_id", "sensor_measure"}
        if run["scenario_description"] == SCENARIO2:
            assert body["sensor_unique_id"] == SENSOR_ID1
            assert body["sensor_measure"] == {"name": "temperature", "units": "Kelvin"}
        else:
            assert body["sensor_unique_id"] is None
            assert body["sensor_measure"] is None


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_unauthorized(client: TestClient, app: FastAPI) -> None:
    """Check that we aren't able to access any of the end points if we don't have an
    authorization token.

    Note that this one, unlike all the others, uses the `client` rather than the
    `auth_client` fixture.
    """

    for route in app.routes:
        if not isinstance(route, Route):
            # For some reason, FastAPI type-annotates app.routes as Sequence[BaseRoute],
            # rather than Sequence[Route]. In case we ever encounter a router isn't a
            # Route, raise an error.
            raise ValueError(f"route {route} is not a Route")
        methods = route.methods
        if methods is None:
            continue
        methods = iter(methods)
        if methods and route.path.startswith("/model"):
            method = next(methods)
            assert_unauthorized(client, method.lower(), route.path)
