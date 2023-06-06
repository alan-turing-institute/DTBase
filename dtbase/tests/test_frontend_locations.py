"""
Test that the DTBase locations pages load
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


def test_new_location_schema_get(frontend_client):
    with frontend_client:
        with requests_mock.Mocker() as m:
            m.get("http://localhost:5000/location/list_location_schemas", json=[])
            m.get("http://localhost:5000/location/list_location_identifiers", json=[])
            response = frontend_client.get("/locations/new_location_schema")
            assert response.status_code == 200
            html_content = response.data.decode("utf-8")
            assert "New Location Schema" in html_content


def test_new_location_schema_post(frontend_client):
    with frontend_client:
        with requests_mock.Mocker() as m:
            m.get("http://localhost:5000/location/list_location_schemas", json=[])
            m.get("http://localhost:5000/location/list_location_identifiers", json=[])
            m.post(
                "http://localhost:5000/location/insert_location_schema", status_code=201
            )
            response = frontend_client.post(
                "/locations/new_location_schema",
                data={
                    "name": "loc1",
                    "description": "a location",
                    "identifier_names[]": "x",
                    "identfier_units[]": "m",
                    "identifier_datatype[]": "float",
                    "identifier_existing[]": "",
                },
            )
            with frontend_client.session_transaction() as session:
                flash_message = dict(session["_flashes"])
                assert flash_message["success"] == "Location schema added successfully"
            assert response.status_code == 302


def test_new_location_no_backend(frontend_client):
    with frontend_client:
        response = frontend_client.get("/locations/new_location", follow_redirects=True)
        assert response.status_code == 200
        html_content = response.data.decode("utf-8")
        assert "Backend API not found" in html_content


def test_new_location_get(frontend_client):
    with frontend_client:
        with requests_mock.Mocker() as m:
            m.get("http://localhost:5000/location/list_location_schemas", json=[])
            response = frontend_client.get("/locations/new_location")
            assert response.status_code == 200
            html_content = response.data.decode("utf-8")
            assert "New Location" in html_content


def test_new_location_post(frontend_client):
    with frontend_client:
        with requests_mock.Mocker() as m:
            m.get(
                "http://localhost:5000/location/get_schema_details/xy",
                json={
                    "identifiers": [
                        {"name": "x", "units": "m", "datatype": "float"},
                        {"name": "y", "units": "m", "datatype": "float"},
                    ]
                },
            )
            m.post("http://localhost:5000/location/insert_location/xy", status_code=201)
            response = frontend_client.post(
                "/locations/new_location",
                data={"schema": "xy", "identifier_x": 12.3, "identifier_y": 23.4},
            )
            with frontend_client.session_transaction() as session:
                flash_message = dict(session["_flashes"])
                assert flash_message["success"] == "Location added successfully"
            assert response.status_code == 302


def test_locations_table_no_backend(frontend_client):
    with frontend_client:
        response = frontend_client.get(
            "/locations/locations_table", follow_redirects=True
        )
        assert response.status_code == 200
        html_content = response.data.decode("utf-8")
        assert "Backend API not found" in html_content


def test_locations_table(frontend_client):
    with frontend_client:
        with requests_mock.Mocker() as m:
            m.get(
                "http://localhost:5000/location/list_location_schemas",
                json=[{"name": "xyz"}],
            )
            m.get(
                "http://localhost:5000/location/list/xyz",
                json=[
                    {
                        "name": "loc1",
                        "description": "somewhere",
                        "x": 11.1,
                        "y": 22.2,
                        "z": 33.3,
                    },
                    {
                        "name": "loc2",
                        "description": "somewhere else",
                        "x": 12.3,
                        "y": 21.0,
                        "z": 34.3,
                    },
                ],
            )
            response = frontend_client.get("/locations/locations_table")
            assert response.status_code == 200
            html_content = response.data.decode("utf-8")
            assert "<title>DTBase |  Locations </title>" in html_content
            assert '<div id="locationTable"></div>' in html_content
            assert "loc1" in html_content
            assert "loc2" in html_content
