import time

import pytest
from flask.testing import FlaskClient
from werkzeug.test import Client, TestResponse

from dtbase.backend.api import create_app as create_backend_app
from dtbase.backend.config import config_dict as backend_config
from dtbase.core.constants import SQL_TEST_CONNECTION_STRING, SQL_TEST_DBNAME

# The below import is for exporting, other modules will import it from there
from dtbase.core.db import (
    connect_db,
    create_database,
    create_tables,
    drop_db,
    drop_tables,
    session_close,  # noqa: F401
    session_open,
)

# The below import is for exporting, other modules will import it from there
from dtbase.core.db_docker import (
    check_for_docker,  # noqa: F401
    start_docker_postgres,
    stop_docker_postgres,
)
from dtbase.core.users import insert_user
from dtbase.webapp.app import create_app as create_frontend_app
from dtbase.webapp.config import config_dict as frontend_config

# if we start a new docker container, store the ID so we can stop it later
DOCKER_CONTAINER_ID = None
TEST_USER_EMAIL = "test@test.com"
TEST_USER_PASSWORD = "test"


def get_token(client: Client) -> TestResponse:
    """Get an authentication token for the test user."""
    type_data = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
    }
    response = client.post("/auth/login", json=type_data)
    return response


class AuthenticatedClient(FlaskClient):
    """Like a FlaskClient, but adds an authentication header to all requests."""

    def __init__(self, *args, **kwargs):
        """Initialise a client that behaves exactly like a normal FlaskClient."""
        super().__init__(*args, **kwargs)
        self._headers = {}

    def authenticate(self):
        """Authenticate with the /auth/login endpoint.

        After this method has been called all requests sent by this client will include
        an authentication header with the token.
        """
        response = get_token(self)
        if response.status_code != 200 or response.json is None:
            raise RuntimeError("Failed to authenticate test client.")
        token = response.json["access_token"]
        self._headers = {"Authorization": f"Bearer {token}"}

    def open(self, *args, **kwargs):
        """For any request, append the authentication headers, and call the usual
        request function.

        Note that methods like self.post and self.get all call self.open.
        """
        kwargs["headers"] = kwargs.get("headers", {}) | self._headers
        return super().open(*args, **kwargs)


def reset_tables():
    """Reset the database by dropping all tables and recreating them."""
    status, log, engine = connect_db(SQL_TEST_CONNECTION_STRING, SQL_TEST_DBNAME)
    drop_tables(engine)
    create_tables(engine)


@pytest.fixture()
def frontend_app():
    config = frontend_config["Test"]
    app = create_frontend_app(config)
    yield app


@pytest.fixture()
def frontend_client(frontend_app):
    return frontend_app.test_client()


@pytest.fixture()
def frontend_runner(frontend_app):
    return frontend_app.test_cli_runner()


@pytest.fixture()
def session():
    status, log, engine = connect_db(SQL_TEST_CONNECTION_STRING, SQL_TEST_DBNAME)
    session = session_open(engine)
    yield session
    session.close()
    reset_tables()


@pytest.fixture()
def app():
    config = backend_config["Test"]
    app = create_backend_app(config)
    app.test_client_class = AuthenticatedClient
    yield app
    reset_tables()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def test_user(app, session):
    # create a dummy test user
    with app.app_context():
        insert_user(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD, session=session)
        session.commit()


@pytest.fixture()
def auth_client(client, test_user):
    client.authenticate()
    return client


@pytest.fixture()
def backend_runner(app):
    return app.test_cli_runner()


def pytest_configure():
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


def pytest_unconfigure():
    """
    called before test process is exited.
    """

    print("pytest_unconfigure: start")
    # drops test db
    success, log = drop_db(SQL_TEST_CONNECTION_STRING, SQL_TEST_DBNAME)
    assert success, log
    # if we started a docker container in pytest_configure, kill it here.
    if DOCKER_CONTAINER_ID:
        stop_docker_postgres(DOCKER_CONTAINER_ID)
    print("pytest_unconfigure: end")
