"""
Test that the DTBase services pages load
"""
import requests_mock
from flask.testing import FlaskClient

MOCK_SERVICE_LIST = [
    {"name": "service1", "url": "http://urlurlurl", "http_method": "GET"},
    {"name": "service2", "url": "http://urlurlurl", "http_method": "GET"},
]


def test_services_index_backend(auth_frontend_client: FlaskClient) -> None:
    with auth_frontend_client as client:
        response = client.get("/services/index", follow_redirects=True)
        assert response.status_code == 200
        html_content = response.data.decode("utf-8")
        assert "Add a service" in html_content


def test_services_index_mock(mock_auth_frontend_client: FlaskClient) -> None:
    with mock_auth_frontend_client as client:
        with requests_mock.Mocker() as m:
            m.get(
                "http://localhost:5000/service/list-services",
                json=MOCK_SERVICE_LIST,
            )
            response = client.get("/services/index")
            assert response.status_code == 200
            html_content = response.data.decode("utf-8")
            assert "Add a service" in html_content
            assert "service1" in html_content
            assert "service2" in html_content


def test_service_details_mock(mock_auth_frontend_client: FlaskClient) -> None:
    with mock_auth_frontend_client as client:
        with requests_mock.Mocker() as m:
            m.get(
                "http://localhost:5000/service/list-services",
                json=MOCK_SERVICE_LIST,
            )
            m.post(
                "http://localhost:5000/service/list-parameter-sets",
                json=[
                    {"service_name": "service1", "name": "paramset1", "parameters": {}}
                ],
            )
            m.post(
                "http://localhost:5000/service/list-runs",
                json=[
                    {
                        "service_name": "service1",
                        "parameter_set_name": "paramset1",
                        "parameters": {},
                        "timestamp": "2021-01-01T00:00:00",
                        "response_status_code": 200,
                        "response_json": {"message": "Hello"},
                    }
                ],
            )
            response = client.get("/services/details?service_name=service1")
            assert response.status_code == 200
            html_content = response.data.decode("utf-8")
            assert "service1" in html_content
            assert "Parameters" in html_content
            assert "Saved parameter sets" in html_content
            assert "Run log" in html_content
            assert "paramset1" in html_content
            assert '"Hello"' in html_content
            assert "200 - OK" in html_content
