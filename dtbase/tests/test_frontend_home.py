"""
Test that the DTBase homepage loads
"""
from flask.testing import FlaskClient


def test_home(auth_frontend_client: FlaskClient) -> None:
    with auth_frontend_client as client:
        response = client.get("/home/index")
        assert response.status_code == 200
        html_content = response.data.decode("utf-8")
        assert "Welcome to DTBase" in html_content
