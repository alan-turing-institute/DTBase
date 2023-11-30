"""
Test that the DTBase users pages load
"""
import re

import requests_mock
from flask.testing import FlaskClient


def test_users_index_backend(auth_frontend_client: FlaskClient) -> None:
    with auth_frontend_client as client:
        response = client.get("/users/index", follow_redirects=True)
        assert response.status_code == 200
        html_content = response.data.decode("utf-8")
        assert "List of all users" in html_content

        # Find the password toggle button
        eye_button = re.search(
            r"<i[^>]*id=\"show-password\"[^>]*>", response.data.decode()
        )
        assert eye_button is not None, "Password toggle button not found"


def test_users_index_get_mock(mock_auth_frontend_client: FlaskClient) -> None:
    with mock_auth_frontend_client as client:
        with requests_mock.Mocker() as m:
            m.get(
                "http://localhost:5000/user/list-users",
                json=["user1@example.com", "user2@example.com"],
            )
            response = client.get("/users/index")
            assert response.status_code == 200
            html_content = response.data.decode("utf-8")
            assert "List of all users" in html_content
            assert "user1@example.com" in html_content
            assert "user2@example.com" in html_content


def test_users_index_post_mock_create_user(
    mock_auth_frontend_client: FlaskClient,
) -> None:
    with mock_auth_frontend_client as client:
        with requests_mock.Mocker() as m:
            m.get("http://localhost:5000/user/list-users", json=[])
            m.post("http://localhost:5000/user/create-user", status_code=201)
            response = client.post(
                "/users/index",
                data={
                    "email": "newuser@example.com",
                    "password": "password",
                    "submitNewUser": "",
                },
            )
            assert response.status_code == 200
            html_content = response.data.decode("utf-8")
            assert "User created successfully" in html_content


def test_users_index_post_mock_create_user_fail(
    mock_auth_frontend_client: FlaskClient,
) -> None:
    with mock_auth_frontend_client as client:
        with requests_mock.Mocker() as m:
            m.get("http://localhost:5000/user/list-users", json=[])
            m.post("http://localhost:5000/user/create-user", status_code=500)
            response = client.post(
                "/users/index",
                data={
                    "email": "newuser@example.com",
                    "password": "password",
                    "submitNewUser": "",
                },
            )
            assert response.status_code == 200
            html_content = response.data.decode("utf-8")
            assert "Failed to create user" in html_content


def test_users_index_post_mock_delete_user(
    mock_auth_frontend_client: FlaskClient,
) -> None:
    with mock_auth_frontend_client as client:
        with requests_mock.Mocker() as m:
            m.get("http://localhost:5000/user/list-users", json=["user1@example.com"])
            m.delete("http://localhost:5000/user/delete-user", status_code=200)
            response = client.post(
                "/users/index",
                data={
                    "email": "user1@example.com",
                    "submitDelete": "",
                },
            )
            assert response.status_code == 200
            html_content = response.data.decode("utf-8")
            assert "User deleted successfully" in html_content


def test_users_index_post_mock_delete_user_fail(
    mock_auth_frontend_client: FlaskClient,
) -> None:
    with mock_auth_frontend_client as client:
        with requests_mock.Mocker() as m:
            m.get("http://localhost:5000/user/list-users", json=["user1@example.com"])
            m.delete("http://localhost:5000/user/delete-user", status_code=500)
            response = client.post(
                "/users/index",
                data={
                    "email": "user1@example.com",
                    "submitDelete": "",
                },
            )
            assert response.status_code == 200
            html_content = response.data.decode("utf-8")
            assert "Failed to delete user" in html_content
