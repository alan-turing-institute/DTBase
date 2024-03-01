"""Configuration module for unit tests."""
import time
from html.parser import HTMLParser
from typing import Any, Callable, Generator, Optional
from unittest import mock
from urllib.parse import urlparse

import numpy as np
import pytest
import requests_mock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from flask import Flask
from flask.testing import FlaskClient
from httpx import Response as HTTPXResponse
from requests.models import Response as RequestsResponse
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from dtbase.backend.api import create_app as create_backend_app
from dtbase.core.constants import (
    DEFAULT_USER_EMAIL,
    DEFAULT_USER_PASS,
    SQL_TEST_CONNECTION_STRING,
    SQL_TEST_DBNAME,
)

# The below import is for exporting, other modules will import it from there
from dtbase.core.db import (
    connect_db,
    create_database,
    create_tables,
    drop_db,
    drop_tables,
    session_close,  # noqa: F401
)

# The below import is for exporting, other modules will import it from there
from dtbase.core.db_docker import (
    check_for_docker,  # noqa: F401
    start_docker_postgres,
    stop_docker_postgres,
)
from dtbase.core.users import insert_user
from dtbase.frontend.app import create_app as create_frontend_app
from dtbase.frontend.config import config_dict as frontend_config

from .utils import TEST_USER_EMAIL, TEST_USER_PASSWORD, get_token

np.random.seed(42)

# if we start a new docker container, store the ID so we can stop it later
DOCKER_CONTAINER_ID: Optional[str] = None


class CSRFTokenParser(HTMLParser):
    """HTML parser that finds a CSRF token in a page."""

    def handle_starttag(
        self: "CSRFTokenParser", tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag == "input":
            dict_attrs = dict(attrs)
            if dict_attrs.get("id") == "csrf_token":
                self.csrf_token = dict_attrs["value"]


def get_csrf_token(client: FlaskClient) -> str:
    """Get the CSRF token of the login page of of the frontend.

    This is needed to be able to authenticate with the frontend.
    """
    response = client.get("/login")
    parser = CSRFTokenParser()
    parser.feed(response.data.decode())
    token = parser.csrf_token
    if token is None:
        raise RuntimeError("Failed to extract CSRF token")
    return token


def reset_tables(engine: Engine) -> None:
    """Reset the database by dropping all tables and recreating them."""
    drop_tables(engine)
    create_tables(engine)


@pytest.fixture(scope="session")
def engine() -> Generator[Engine, None, None]:
    """Pytest fixture for a database engine.

    This fixture is session-scoped, meaning that it is created once and shared across
    all tests.
    """
    engine = connect_db(SQL_TEST_CONNECTION_STRING, SQL_TEST_DBNAME)
    with mock.patch("dtbase.backend.db.DB_ENGINE", wraps=engine):
        yield engine


@pytest.fixture(scope="session")
def session_maker(engine: Engine) -> Generator[sessionmaker, None, None]:
    session_maker = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    with mock.patch("dtbase.backend.db.DB_SESSION_MAKER", wraps=session_maker):
        yield session_maker


@pytest.fixture()
def session(
    engine: Engine, session_maker: sessionmaker
) -> Generator[Session, None, None]:
    """Pytest fixture for a database session.

    Handles clean-up of the database after tests finish.
    """
    session = session_maker()
    try:
        yield session
    finally:
        session.close()
        reset_tables(engine)


@pytest.fixture()
def app(engine: Engine) -> Generator[FastAPI, None, None]:
    """Pytest fixture for a backend app.

    Cleans up the database after finishing.
    """
    app = create_backend_app()
    yield app
    reset_tables(engine)


@pytest.fixture()
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    """Pytest fixture for a client for the backend app."""
    with TestClient(app) as client:
        yield client


@pytest.fixture()
def test_user(session: Session) -> None:
    """Pytest fixture that ensures that there is a test user in the database."""
    try:
        insert_user(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD, session=session)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e


@pytest.fixture()
def auth_client(client: TestClient, test_user: None) -> TestClient:
    """Pytest fixture for a client for the backend app that is authenticated, and uses
    its credentials in all requests it makes.
    """
    response = get_token(client)
    if response.status_code != 200 or response.json is None:
        raise RuntimeError("Failed to authenticate test client.")
    token = response.json()["access_token"]
    client.headers = {"Authorization": f"Bearer {token}"}
    return client


def httpx_to_requests_response(httpx_response: HTTPXResponse) -> RequestsResponse:
    """Convert a httpx.Response into a requests.models.Response."""
    response = RequestsResponse()
    response.status_code = httpx_response.status_code
    response._content = httpx_response.content
    response.headers = {**httpx_response.headers}
    return response


def mock_request_method_builder(
    client: TestClient, method_name: str
) -> Callable[..., RequestsResponse]:
    """Return a function that has the same interface as one of the methods of `requests`
    but behind the scenes actually sends the request to the TestClient `client`.
    `method_name` can be e.g. `"get"` or `"post"`

    The functions returned by this function can be used to make a mocked version of
    requests to reroute any class made to e.g. `requests.get` to a Flask app directly.
    """
    request_func = getattr(client, method_name)

    def method(url: str, *args: Any, **kwargs: Any) -> RequestsResponse:
        endpoint = urlparse(url).path
        response = httpx_to_requests_response(request_func(endpoint, *args, **kwargs))
        return response

    return method


@pytest.fixture()
def frontend_app() -> Flask:
    """Pytest fixture for a Flask app for the front end."""
    config = frontend_config["Test"]
    # This would usually be set by an environment variable, but for tests we hardcode
    # it.
    config.SECRET_KEY = "the world's third worst kept secret"
    frontend_app = create_frontend_app(config)
    return frontend_app


@pytest.fixture()
def frontend_client(frontend_app: Flask) -> FlaskClient:
    """Pytest fixture for a client for a Flask app for the front end."""
    return frontend_app.test_client()


@pytest.fixture()
def mock_auth_frontend_client(frontend_client: FlaskClient) -> FlaskClient:
    """Pytest fixture for front end client that acts as if the user has logged in,
    although there is no backend to actually connect to.
    """
    with requests_mock.Mocker() as m:
        m.post(
            "http://localhost:5000/auth/login",
            json={
                "access_token": "mock access token",
                "refresh_token": "mock refresh token",
            },
        )
        csrf_token = get_csrf_token(frontend_client)
        payload = {
            "email": DEFAULT_USER_EMAIL,
            "password": DEFAULT_USER_PASS,
            "csrf_token": csrf_token,
        }
        frontend_client.post("/login", data=payload)
    return frontend_client


@pytest.fixture()
def conn_frontend_app(
    frontend_app: Flask, client: TestClient
) -> Generator[Flask, None, None]:
    """Pytest fixture for a frontend Flask app that is connected to a backend.

    This fixture also spins up a testing backend and routes any calls made through
    `requests` to this backend.
    """
    mock_requests = mock.MagicMock()
    for method_name in ("get", "post", "put", "delete"):
        mock_method = mock_request_method_builder(client, method_name)
        setattr(mock_requests, method_name, mock_method)

    with mock.patch("dtbase.core.utils.requests", wraps=mock_requests):
        config = frontend_config["Test"]
        frontend_app = create_frontend_app(config)
        yield frontend_app


@pytest.fixture()
def conn_frontend_client(conn_frontend_app: Flask) -> FlaskClient:
    """Pytest fixture for a client for a frontend connected to a backend."""
    return conn_frontend_app.test_client()


@pytest.fixture()
def auth_frontend_client(conn_frontend_client: FlaskClient) -> FlaskClient:
    """Pytest fixture for a client for a frontend that is a connected to a backend and
    with the user logged in.
    """
    csrf_token = get_csrf_token(conn_frontend_client)
    payload = {
        "email": DEFAULT_USER_EMAIL,
        "password": DEFAULT_USER_PASS,
        "csrf_token": csrf_token,
    }
    conn_frontend_client.post("/login", data=payload)
    return conn_frontend_client


@pytest.fixture()
def conn_backend(
    client: TestClient,
) -> Generator[TestClient, None, None]:
    """Pytest fixture setting up a backend and making core.utils.backend_call talk to it

    This works by mocking dtbase.models.utils.backend_call.requests with an object that
    reroutes all calls to a test backend client.

    `yields` the backend client.
    """
    mock_requests = mock.MagicMock()
    for method_name in ("get", "post", "put", "delete"):
        mock_method = mock_request_method_builder(client, method_name)
        setattr(mock_requests, method_name, mock_method)

    with mock.patch("dtbase.core.utils.requests", wraps=mock_requests):
        yield client


def pytest_configure() -> None:
    """
    Allows plugins and conftest files to perform initial configuration.
    This hook is called for every plugin and initial conftest
    file after command line options have been parsed.
    """

    # move on with the rest of the setup
    print(
        "pytest_configure: start " + SQL_TEST_CONNECTION_STRING + " " + SQL_TEST_DBNAME
    )
    global DOCKER_CONTAINER_ID
    DOCKER_CONTAINER_ID = start_docker_postgres()
    if DOCKER_CONTAINER_ID:
        print(f"Setting DOCKER_CONTAINER_ID to {DOCKER_CONTAINER_ID}")
    # create database so that we have tables ready
    create_database(SQL_TEST_CONNECTION_STRING, SQL_TEST_DBNAME)
    time.sleep(1)
    #    upload_synthetic_data.main(SQL_TEST_DBNAME)
    print("pytest_configure: end")


def pytest_unconfigure() -> None:
    """
    called before test process is exited.
    """

    print("pytest_unconfigure: start")
    # drops test db
    drop_db(SQL_TEST_CONNECTION_STRING, SQL_TEST_DBNAME)
    # if we started a docker container in pytest_configure, kill it here.
    if DOCKER_CONTAINER_ID:
        stop_docker_postgres(DOCKER_CONTAINER_ID)
    print("pytest_unconfigure: end")
