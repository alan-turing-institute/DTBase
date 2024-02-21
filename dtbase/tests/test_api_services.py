"""
Test API endpoints for services.
"""
import datetime as dt
from unittest import mock

import pytest
import requests_mock
from dateutil.parser import parse
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.routing import Route

from dtbase.tests.conftest import check_for_docker
from dtbase.tests.utils import assert_unauthorized

DOCKER_RUNNING = check_for_docker()

SERVICE1 = {
    "name": "Get me some milk",
    "url": "http://dairyland.com/milk",
    "http_method": "GET",
}

SERVICE2 = {
    "name": "Collect honey",
    "url": "http://beesknees.net/nectar-of-the-gods",
    "http_method": "POST",
}

UNNAMED_PARAMETERS1 = {
    "service_name": "Get me some milk",
    "parameters": {"milk_type": "whole", "quantity": 1},
}

NAMED_PARAMETERS1 = {
    "service_name": "Get me some milk",
    "name": "Half a pint of skimmed",
    "parameters": {"milk_type": "skimmed", "quantity": 0.5},
}

NAMED_PARAMETERS2 = {
    "service_name": "Collect honey",
    "name": "Lavender",
    "parameters": {"honey_type": "lavender"},
}


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_insert_service(auth_client: TestClient) -> None:
    response = auth_client.post("/service/insert-service", json=SERVICE1)
    assert response.status_code == 201


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_list_services(auth_client: TestClient) -> None:
    auth_client.post("/service/insert-service", json=SERVICE1)
    auth_client.post("/service/insert-service", json=SERVICE2)
    response = auth_client.get("/service/list-services")
    assert response.status_code == 200
    assert response.json() == [SERVICE1, SERVICE2]


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_delete_service(auth_client: TestClient) -> None:
    auth_client.post("/service/insert-service", json=SERVICE1)
    auth_client.post("/service/insert-service", json=SERVICE2)
    auth_client.post("/service/delete-service", json={"name": SERVICE1["name"]})
    response = auth_client.get("/service/list-services")
    assert response.status_code == 200
    assert response.json() == [SERVICE2]


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_insert_parameter_set(auth_client: TestClient) -> None:
    auth_client.post("/service/insert-service", json=SERVICE1)
    response = auth_client.post("/service/insert-parameter-set", json=NAMED_PARAMETERS1)
    assert response.status_code == 201


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_list_parameter_sets(auth_client: TestClient) -> None:
    auth_client.post("/service/insert-service", json=SERVICE1)
    auth_client.post("/service/insert-service", json=SERVICE2)
    auth_client.post("/service/insert-parameter-set", json=NAMED_PARAMETERS1)
    auth_client.post("/service/insert-parameter-set", json=NAMED_PARAMETERS2)
    response = auth_client.post("/service/list-parameter-sets")
    assert response.status_code == 200
    assert response.json() == [NAMED_PARAMETERS1, NAMED_PARAMETERS2]
    response = auth_client.post(
        "/service/list-parameter-sets", json={"service_name": SERVICE1["name"]}
    )
    assert response.status_code == 200
    assert response.json() == [NAMED_PARAMETERS1]


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_edit_parameter_set(auth_client: TestClient) -> None:
    auth_client.post("/service/insert-service", json=SERVICE1)
    auth_client.post("/service/insert-service", json=SERVICE2)
    auth_client.post("/service/insert-parameter-set", json=NAMED_PARAMETERS1)
    auth_client.post("/service/insert-parameter-set", json=NAMED_PARAMETERS2)
    edited_parameters = NAMED_PARAMETERS1.copy()
    edited_parameters["parameters"]["quantity"] = 1.5
    response = auth_client.post("/service/edit-parameter-set", json=edited_parameters)
    assert response.status_code == 200
    response = auth_client.post("/service/list-parameter-sets")
    assert response.status_code == 200
    response_json = response.json()
    assert edited_parameters in response_json


def test_run_service_named_parameters(auth_client: TestClient) -> None:
    auth_client.post("/service/insert-service", json=SERVICE1)
    auth_client.post("/service/insert-parameter-set", json=NAMED_PARAMETERS1)
    with requests_mock.Mocker() as m:
        m.get(SERVICE1["url"], json={"message": "Here's your milk"})
        response = auth_client.post(
            "/service/run-service",
            json={
                "service_name": NAMED_PARAMETERS1["service_name"],
                "parameter_set_name": NAMED_PARAMETERS1["name"],
            },
        )
        assert response.status_code == 200


def test_run_service_unnamed_parameters(auth_client: TestClient) -> None:
    auth_client.post("/service/insert-service", json=SERVICE1)
    with requests_mock.Mocker() as m:
        m.get(SERVICE1["url"], json={"message": "Here's your milk"})
        response = auth_client.post("/service/run-service", json=UNNAMED_PARAMETERS1)
    assert response.status_code == 200


def test_list_runs(auth_client: TestClient) -> None:
    auth_client.post("/service/insert-service", json=SERVICE1)
    auth_client.post("/service/insert-service", json=SERVICE2)
    auth_client.post("/service/insert-parameter-set", json=NAMED_PARAMETERS1)
    auth_client.post("/service/insert-parameter-set", json=NAMED_PARAMETERS2)

    now = dt.datetime(2021, 1, 1, tzinfo=dt.timezone.utc)
    with requests_mock.Mocker() as m, mock.patch("dtbase.core.service.dt") as mock_dt:
        mock_dt.datetime.now.return_value = now
        m.get(SERVICE1["url"], json={"message": "Here's your milk"})
        m.post(SERVICE2["url"], json={"message": "Here's your honey"}, status_code=201)
        auth_client.post(
            "/service/run-service",
            json={
                "service_name": NAMED_PARAMETERS1["service_name"],
                "parameter_set_name": NAMED_PARAMETERS1["name"],
            },
        )
        auth_client.post("/service/run-service", json=UNNAMED_PARAMETERS1)
        auth_client.post(
            "/service/run-service",
            json={
                "service_name": NAMED_PARAMETERS2["service_name"],
                "parameter_set_name": NAMED_PARAMETERS2["name"],
            },
        )
        auth_client.post(
            "/service/run-service",
            json={
                "service_name": NAMED_PARAMETERS1["service_name"],
                "parameter_set_name": NAMED_PARAMETERS1["name"],
            },
        )

    response = auth_client.post("/service/list-runs", json={})
    assert response.status_code == 200
    response_json = response.json()
    for run in response_json:
        run["timestamp"] = parse(run["timestamp"])

    expected_runs = [
        {
            "service_name": NAMED_PARAMETERS1["service_name"],
            "parameter_set_name": NAMED_PARAMETERS1["name"],
            "parameters": NAMED_PARAMETERS1["parameters"],
            "response_json": {"message": "Here's your milk"},
            "response_status_code": 200,
            "timestamp": now,
        },
        {
            "service_name": UNNAMED_PARAMETERS1["service_name"],
            "parameter_set_name": None,
            "parameters": UNNAMED_PARAMETERS1["parameters"],
            "response_json": {"message": "Here's your milk"},
            "response_status_code": 200,
            "timestamp": now,
        },
        {
            "service_name": NAMED_PARAMETERS2["service_name"],
            "parameter_set_name": NAMED_PARAMETERS2["name"],
            "parameters": NAMED_PARAMETERS2["parameters"],
            "response_json": {"message": "Here's your honey"},
            "response_status_code": 201,
            "timestamp": now,
        },
        {
            "service_name": NAMED_PARAMETERS1["service_name"],
            "parameter_set_name": NAMED_PARAMETERS1["name"],
            "parameters": NAMED_PARAMETERS1["parameters"],
            "response_json": {"message": "Here's your milk"},
            "response_status_code": 200,
            "timestamp": now,
        },
    ]
    for expected_run in expected_runs:
        assert expected_run in response_json


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
        if not methods or not route.path.startswith("/service"):
            continue
        for method in methods:
            assert_unauthorized(client, method.lower(), route.path)
