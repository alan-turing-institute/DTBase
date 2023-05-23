"""
Test that the DTBase sensors pages load
"""
from flask import url_for, request
import pytest
import requests_mock


def test_new_location_schema_no_backend(frontend_client):
    with frontend_client:
        response = frontend_client.get(
            "/locations/new_location_schema", follow_redirects=True
        )
        assert response.status_code == 200
        html_content = response.data.decode("utf-8")
        assert "Backend API not found" in html_content


def test_new_location_schema(frontend_client):
    with frontend_client:
        with requests_mock.Mocker() as m:
            m.get("http://localhost:5000/location/list_location_schemas", json=[])
            m.get("http://localhost:5000/location/list_location_identifiers", json=[])
            response = frontend_client.get("/locations/new_location_schema")
            assert response.status_code == 200
            html_content = response.data.decode("utf-8")
            assert "New Location Schema" in html_content
