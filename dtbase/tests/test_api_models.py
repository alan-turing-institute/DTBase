"""
Test API endpoints for models
"""
import datetime as dt

import json
import pytest
from unittest import mock

from dtbase.tests.conftest import check_for_docker
from dtbase.backend.api.sensor import routes

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

PRODUCT1 = {
    "measure_name": MEASURE_NAME1,
    "values": [-23.0, -23.0, -23.1],
    "timestamps": [
        NOW + dt.timedelta(days=1),
        NOW + dt.timedelta(days=2),
        NOW + dt.timedelta(days=3),
    ],
}
PRODUCT2 = {
    "measure_name": MEASURE_NAME2,
    "values": [True, True, True],
    "timestamps": [
        NOW + dt.timedelta(days=1),
        NOW + dt.timedelta(days=2),
        NOW + dt.timedelta(days=3),
    ],
}
PRODUCT3 = {
    "measure_name": MEASURE_NAME2,
    "values": [False, True, False],
    "timestamps": [
        NOW + dt.timedelta(weeks=1),
        NOW + dt.timedelta(weeks=2),
        NOW + dt.timedelta(weeks=3),
    ],
}


def insert_model_measures(client):
    response1 = client.post("/model/insert_model_measure", json=json.dumps(MEASURE1))
    response2 = client.post("/model/insert_model_measure", json=json.dumps(MEASURE2))
    return response1, response2


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_insert_model(client):
    with client:
        model = {"name": "test model"}
        response = client.post("/model/insert_model", json=json.dumps(model))
        assert response.status_code == 201


# @pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
# def test_list_models(client):
#     with client:
#         response = client.post("/model/insert_model", json=json.dumps({"name": "test model 1"}))
#         assert response.status_code == 201
#         response = client.post("/model/insert_model", json=json.dumps({"name": "test model 2"}))
#         assert response.status_code == 201

#         response = client.get("/model/list_models")
#         assert response.status_code == 200
#         assert isinstance(response.json, list)
#         # check that list is of length 2
#         assert len(response.json) == 2
#         print(response.json)


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_insert_model_measures(client):
    with client:
        responses = insert_model_measures(client)
        for response in responses:
            assert response.status_code == 201


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_list_model_measures(client):
    with client:
        insert_model_measures(client)
        response = client.get("/model/list_model_measures")
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
def test_delete_model_measures(client):
    with client:
        insert_model_measures(client)
        response = client.delete(
            "/model/delete_model_measure",
            json=json.dumps({"name": MEASURE_NAME1}),
        )
        assert response.status_code == 200
        response = client.get("/model/list_model_measures")
        response_data = response.json
        assert len(response_data) == 1
