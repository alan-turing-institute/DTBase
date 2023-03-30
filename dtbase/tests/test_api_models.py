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
        # add two models
        response = client.post("/model/insert_model", json=json.dumps({"name": "test model 1"}))
        assert response.status_code == 201
        response = client.post("/model/insert_model", json=json.dumps({"name": "test model 2"}))
        assert response.status_code == 201
        
        # list models
        response = client.get("/model/list_models")
        assert response.status_code == 200
        assert isinstance(response.json, list)
        assert len(response.json) == 2


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_delete_model(client):
    with client:
        # add a model
        response = client.post("/model/insert_model", json=json.dumps({"name": "test model"}))
        assert response.status_code == 201
        
        # delete model
        response = client.delete("/model/delete_model", json=json.dumps({"name": "test model"}))
        assert response.status_code == 200
        
        # check that model was deleted
        response = client.get("/model/list_models")
        assert response.status_code == 200
        assert isinstance(response.json, list)
        assert len(response.json) == 0


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_insert_model_scenario(client):
    with client:
        # add a model
        response = client.post("/model/insert_model", json=json.dumps({"name": "test model"}))
        assert response.status_code == 201
        
        # add a model scenario
        model_scenario = {"model_name": "test model", "description": "test scenario"}
        response = client.post("/model/insert_model_scenario", json=json.dumps(model_scenario))
        assert response.status_code == 201


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_list_model_scenarios(client):
    with client:
        # add a model
        response = client.post("/model/insert_model", json=json.dumps({"name": "test model"}))
        assert response.status_code == 201
        
        # add a model scenario
        model_scenario = {"model_name": "test model", "description": "test scenario"}
        response = client.post("/model/insert_model_scenario", json=json.dumps(model_scenario))
        assert response.status_code == 201
        
        # add a second model scenario
        model_scenario = {"model_name": "test model", "description": "test scenario 2"}
        response = client.post("/model/insert_model_scenario", json=json.dumps(model_scenario))
        assert response.status_code == 201
        
        # list model scenarios
        response = client.get("/model/list_model_scenarios")
        assert response.status_code == 200
        assert isinstance(response.json, list)
        assert len(response.json) == 2
        
        
@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_delete_model_scenario(client):
    with client:
        # add a model
        response = client.post("/model/insert_model", json=json.dumps({"name": "test model"}))
        assert response.status_code == 201
        
        # add a model scenario
        model_scenario = {"model_name": "test model", "description": "test scenario"}
        response = client.post("/model/insert_model_scenario", json=json.dumps(model_scenario))
        assert response.status_code == 201
        
        # delete model scenario
        response = client.delete("/model/delete_model_scenario", json=json.dumps({"model_name": "test model", "description": "test scenario"}))
        assert response.status_code == 200
        
        # check that model scenario was deleted
        response = client.get("/model/list_model_scenarios")
        assert response.status_code == 200
        assert isinstance(response.json, list)
        assert len(response.json) == 0
