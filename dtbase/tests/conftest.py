import os
import time

import pytest

from dtbase.backend.api import create_app as create_backend_app
from dtbase.backend.config import config_dict as backend_config
from dtbase.core.constants import SQL_TEST_CONNECTION_STRING, SQL_TEST_DBNAME
from dtbase.core.db import (
    connect_db,
    create_database,
    create_tables,
    drop_db,
    drop_tables,
    session_close,
    session_open,
)
from dtbase.core.db_docker import (
    check_for_docker,
    start_docker_postgres,
    stop_docker_postgres,
)
from dtbase.core.utils import create_user
from dtbase.webapp.app import create_app as create_frontend_app
from dtbase.webapp.config import config_dict as frontend_config


# if we start a new docker container, store the ID so we can stop it later
DOCKER_CONTAINER_ID = None


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
    yield app
    reset_tables()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def testuser(app):
    # create a dummy test user
    with app.app_context():
        create_user(username="testuser", email="test@test.com", password="test")


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
