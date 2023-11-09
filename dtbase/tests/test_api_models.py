"""
Test API endpoints for models
"""
import datetime as dt

import pytest
from flask.testing import FlaskClient

from dtbase.tests.conftest import check_for_docker

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


def insert_model(client: FlaskClient, name: str) -> None:
    response = client.post("/model/insert-model", json={"name": name})
    assert response.status_code == 201


def insert_model_measures(client: FlaskClient) -> None:
    response1 = client.post("/model/insert-model-measure", json=MEASURE1)
    response2 = client.post("/model/insert-model-measure", json=MEASURE2)
    return response1, response2


def insert_model_scenarios(client: FlaskClient) -> None:
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


def insert_model_runs(client: FlaskClient) -> None:
    insert_model_measures(client)
    insert_model_scenarios(client)
    run1 = {
        "model_name": MODEL_NAME1,
        "scenario_description": SCENARIO1,
        "measures_and_values": [PRODUCT1],
    }
    run2 = {
        "model_name": MODEL_NAME1,
        "scenario_description": SCENARIO2,
        "measures_and_values": [PRODUCT2],
        "time_created": (NOW - dt.timedelta(days=7)).isoformat(),
    }
    run3 = {
        "model_name": MODEL_NAME2,
        "scenario_description": SCENARIO3,
        "measures_and_values": [PRODUCT3],
        "create_scenario": True,
    }
    response1 = client.post("/model/insert-model-run", json=run1)
    response2 = client.post("/model/insert-model-run", json=run2)
    response3 = client.post("/model/insert-model-run", json=run3)
    return response1, response2, response3


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_insert_model(client: FlaskClient) -> None:
    with client:
        model = {"name": MODEL_NAME1}
        response = client.post("/model/insert-model", json=model)
        assert response.status_code == 201


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_list_models(client: FlaskClient) -> None:
    with client:
        # add two models
        insert_model(client, MODEL_NAME1)
        insert_model(client, MODEL_NAME2)

        # list models
        response = client.get("/model/list-models")
        assert response.status_code == 200
        assert isinstance(response.json, list)
        assert len(response.json) == 2


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_delete_model(client: FlaskClient) -> None:
    with client:
        # add a model
        insert_model(client, MODEL_NAME1)

        # delete model
        response = client.delete("/model/delete-model", json={"name": MODEL_NAME1})
        assert response.status_code == 200

        # check that model was deleted
        response = client.get("/model/list-models")
        assert response.status_code == 200
        assert isinstance(response.json, list)
        assert len(response.json) == 0


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_insert_model_scenario(client: FlaskClient) -> None:
    with client:
        # add a model scenario
        responses = insert_model_scenarios(client)
        for response in responses:
            assert response.status_code == 201


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_list_model_scenarios(client: FlaskClient) -> None:
    with client:
        # add a model scenario
        insert_model_scenarios(client)
        # list model scenarios
        response = client.get("/model/list-model-scenarios")
        assert response.status_code == 200
        assert isinstance(response.json, list)
        assert len(response.json) == 3


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_delete_model_scenario(client: FlaskClient) -> None:
    with client:
        # add a model scenario
        insert_model_scenarios(client)
        # delete model scenario
        response = client.delete(
            "/model/delete-model-scenario",
            json={"model_name": MODEL_NAME1, "description": SCENARIO1},
        )
        assert response.status_code == 200

        # check that model scenario was deleted
        response = client.get("/model/list-model-scenarios")
        assert response.status_code == 200
        assert isinstance(response.json, list)
        assert len(response.json) == 2


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_insert_model_measures(client: FlaskClient) -> None:
    with client:
        responses = insert_model_measures(client)
        for response in responses:
            assert response.status_code == 201


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_list_model_measures(client: FlaskClient) -> None:
    with client:
        insert_model_measures(client)
        response = client.get("/model/list-model-measures")
        assert response.status_code == 200
        response_data = response.json
        assert len(response_data) == 2
        expected_keys = {"name", "units", "datatype", "id"}
        assert set(response_data[0].keys()) == expected_keys
        assert set(response_data[1].keys()) == expected_keys
        for k, v in MEASURE1.items():
            assert response_data[0][k] == v
        for k, v in MEASURE2.items():
            assert response_data[1][k] == v


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_delete_model_measures(client: FlaskClient) -> None:
    with client:
        insert_model_measures(client)
        response = client.delete(
            "/model/delete-model-measure",
            json={"name": MEASURE_NAME1},
        )
        assert response.status_code == 200
        response = client.get("/model/list-model-measures")
        response_data = response.json
        assert len(response_data) == 1


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_insert_model_runs(client: FlaskClient) -> None:
    with client:
        responses = insert_model_runs(client)
        for response in responses:
            assert response.status_code == 201


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_list_model_runs(client: FlaskClient) -> None:
    with client:
        responses = insert_model_runs(client)

        runs = {
            "model_name": MODEL_NAME1,
            "dt_from": NOW.isoformat(),
            "dt_to": (NOW + dt.timedelta(days=10)).isoformat(),
            "scenario": SCENARIO1,
        }

        responses = client.get("/model/list-model-runs", json=runs)

        assert responses.status_code == 200
        assert isinstance(responses.json, list)
        assert len(responses.json) == 1


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_get_model_run(client: FlaskClient) -> None:
    with client:
        responses = insert_model_runs(client)

        runs = {
            "model_name": MODEL_NAME1,
            "dt_from": NOW.isoformat(),
            "dt_to": (NOW + dt.timedelta(days=10)).isoformat(),
            "scenario": SCENARIO1,
        }
        responses = client.get("/model/list-model-runs", json=runs)
        print(responses.json[0]["id"])
        run_id = responses.json[0]["id"]

        run = {
            "run_id": run_id,
            # "measure_name": MEASURE_NAME1,
        }

        responses = client.get("/model/get-model-run", json=run)
        assert responses.status_code == 200
