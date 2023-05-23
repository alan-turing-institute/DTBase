"""
Test that the DTBase models pages load
"""
from flask import url_for, request
import pytest
import requests_mock


def test_models_index_no_backend(frontend_client):
    with frontend_client:
        response = frontend_client.get("/models/index", follow_redirects=True)
        assert response.status_code == 200
        html_content = response.data.decode("utf-8")
        assert "Backend API not found" in html_content


def test_models_no_models(frontend_client):
    with frontend_client:
        with requests_mock.Mocker() as m:
            m.get("http://localhost:5000/model/list_models", json=[])
            m.get("http://localhost:5000/model/list_model_runs", json=[])
            response = frontend_client.get("/models/index")
            assert response.status_code == 200
            html_content = response.data.decode("utf-8")
            assert "Choose predictive model" in html_content
