"""
Test that the DTBase homepage loads
"""
from flask.testing import FlaskClient


def test_home(frontend_client: FlaskClient) -> None:
    response = frontend_client.get("/home/index")
    assert response.status_code == 200
    html_content = response.data.decode("utf-8")
    assert "Welcome to DTBase" in html_content
