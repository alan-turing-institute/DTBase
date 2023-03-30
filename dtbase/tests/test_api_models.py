"""
Test API endpoints for models
"""

import json
import pytest
from unittest import mock

from dtbase.tests.conftest import check_for_docker
from dtbase.backend.api.sensor import routes

DOCKER_RUNNING = check_for_docker()


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_insert_model(client):
    with client:
        model = {"name": "test model"}
        response = client.post("/model/insert_model", json=json.dumps(model))
        assert response.status_code == 201
        

@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_list_models(client):
    with client:
        response = client.post("/model/insert_model", json=json.dumps({"name": "test model 1"}))
        assert response.status_code == 201
        response = client.post("/model/insert_model", json=json.dumps({"name": "test model 2"}))
        assert response.status_code == 201
        
        response = client.get("/model/list_models")
        assert response.status_code == 200
        assert isinstance(response.json, list)
        assert len(response.json) == 2
    