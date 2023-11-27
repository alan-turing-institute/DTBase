"""
Test that the DTBase locations pages load
"""
import requests_mock
from flask.testing import FlaskClient


def test_new_location_schema_backend(auth_frontend_client: FlaskClient) -> None:
    with auth_frontend_client as client:
        response = client.get("/locations/new-location-schema", follow_redirects=True)
        assert response.status_code == 200
        html_content = response.data.decode("utf-8")
        assert "Enter New Location Schema" in html_content


def test_new_location_schema_get_mock(mock_auth_frontend_client: FlaskClient) -> None:
    with mock_auth_frontend_client as client:
        with requests_mock.Mocker() as m:
            m.get("http://localhost:5000/location/list-location-schemas", json=[])
            m.get("http://localhost:5000/location/list-location-identifiers", json=[])
            response = client.get("/locations/new-location-schema")
            assert response.status_code == 200
            html_content = response.data.decode("utf-8")
            assert "Enter New Location Schema" in html_content


def test_new_location_schema_post_mock(mock_auth_frontend_client: FlaskClient) -> None:
    with mock_auth_frontend_client as client:
        with requests_mock.Mocker() as m:
            m.get("http://localhost:5000/location/list-location-schemas", json=[])
            m.get("http://localhost:5000/location/list-location-identifiers", json=[])
            m.post(
                "http://localhost:5000/location/insert-location-schema", status_code=201
            )
            response = client.post(
                "/locations/new-location-schema",
                data={
                    "name": "loc1",
                    "description": "a location",
                    "identifier_names[]": "x",
                    "identfier_units[]": "m",
                    "identifier_datatype[]": "float",
                    "identifier_existing[]": "",
                },
            )
            with client.session_transaction() as session:
                flash_message = dict(session["_flashes"])
                assert flash_message["success"] == "Location schema added successfully"
            assert response.status_code == 302


def test_new_location_backend(auth_frontend_client: FlaskClient) -> None:
    with auth_frontend_client as client:
        response = client.get("/locations/new-location", follow_redirects=True)
        assert response.status_code == 200
        html_content = response.data.decode("utf-8")
        assert "Add New Location" in html_content


def test_new_location_get_mock(mock_auth_frontend_client: FlaskClient) -> None:
    with mock_auth_frontend_client as client:
        with requests_mock.Mocker() as m:
            m.get("http://localhost:5000/location/list-location-schemas", json=[])
            response = client.get("/locations/new-location")
            assert response.status_code == 200
            html_content = response.data.decode("utf-8")
            assert "Add New Location" in html_content


def test_new_location_post_mock(mock_auth_frontend_client: FlaskClient) -> None:
    with mock_auth_frontend_client as client:
        with requests_mock.Mocker() as m:
            m.get(
                "http://localhost:5000/location/get-schema-details",
                json={
                    "location_schema": "xy",
                    "identifiers": [
                        {"name": "x", "units": "m", "datatype": "float"},
                        {"name": "y", "units": "m", "datatype": "float"},
                    ],
                },
            )
            m.post(
                "http://localhost:5000/location/insert-location-for-schema",
                status_code=201,
            )
            response = client.post(
                "/locations/new-location",
                data={"schema": "xy", "identifier_x": 12.3, "identifier_y": 23.4},
            )
            with client.session_transaction() as session:
                flash_message = dict(session["_flashes"])
                assert flash_message["success"] == "Location added successfully"
            assert response.status_code == 302


def test_locations_table_backend(auth_frontend_client: FlaskClient) -> None:
    with auth_frontend_client as client:
        response = client.get("/locations/locations-table", follow_redirects=True)
        assert response.status_code == 200
        html_content = response.data.decode("utf-8")
        assert "Locations" in html_content


def test_locations_table_mock(mock_auth_frontend_client: FlaskClient) -> None:
    with mock_auth_frontend_client as client:
        with requests_mock.Mocker() as m:
            m.get(
                "http://localhost:5000/location/list-location-schemas",
                json=[{"name": "xyz"}],
            )
            m.get(
                "http://localhost:5000/location/list-locations",
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
            response = client.get("/locations/locations-table")
            assert response.status_code == 200
            html_content = response.data.decode("utf-8")
            assert "<title>DTBase |  Locations </title>" in html_content
            assert '<div id="locationTable"></div>' in html_content
            assert "loc1" in html_content
            assert "loc2" in html_content
