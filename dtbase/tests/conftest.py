import os
import re
import subprocess
import sys
import time

import pytest

from dtbase.backend.api import create_app
from dtbase.backend.config import config_dict
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
from dtbase.core.utils import create_user


# if we start a new docker container, store the ID so we can stop it later
DOCKER_CONTAINER_ID = None


def reset_tables():
    """Reset the database by dropping all tables and recreating them."""
    status, log, engine = connect_db(SQL_TEST_CONNECTION_STRING, SQL_TEST_DBNAME)
    drop_tables(engine)
    create_tables(engine)


@pytest.fixture()
def session():
    status, log, engine = connect_db(SQL_TEST_CONNECTION_STRING, SQL_TEST_DBNAME)
    session = session_open(engine)
    yield session
    session.close()
    reset_tables()


@pytest.fixture()
def rollback_session(session):
    # session.begin()
    yield session
    # session.rollback()
    session.close()
    reset_tables()


@pytest.fixture()
def app():
    config = config_dict["Test"]
    app = create_app(config)
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
def runner(app):
    return app.test_cli_runner()


def check_for_docker():
    """
    See if we have a postgres docker container already running.

    Returns
    =======
    container_id:str if container running,
    OR
    True if docker is running, but no postgres container
    OR
    False if docker is not running
    """
    p = subprocess.run(["docker", "ps"], capture_output=True)
    if p.returncode != 0:
        return False
    output = p.stdout.decode("utf-8")
    m = re.search("([0-9a-f]+)[\s]+postgres", output)
    if not m:
        return True  # Docker is running, but no postgres container
    else:
        return m.groups()[0]  # return the container ID


def pytest_configure(config):
    """
    Allows plugins and conftest files to perform initial configuration.
    This hook is called for every plugin and initial conftest
    file after command line options have been parsed.
    """
    # see if docker is running, and if so, if postgres container exists
    docker_info = check_for_docker()
    if not docker_info:  # docker desktop not running at all
        DOCKER_RUNNING = False
        print("Docker not found - will skip tests that use the database.")
        return
    DOCKER_RUNNING = True
    if isinstance(docker_info, bool):
        # docker is running, but no postgres container
        print("Starting postgres docker container")
        p = subprocess.run(
            [
                "docker",
                "run",
                "-e",
                "POSTGRES_DB=dtdb",
                "-e",
                "POSTGRES_USER=postgres",
                "-e",
                "POSTGRES_PASSWORD=postgres",
                "-d",
                "-p",
                "5432:5432",
                "postgres:11",
            ],
            capture_output=True,
        )
        if p.returncode != 0:
            print("Problem starting Docker container - is Docker running?")
            return
        else:
            # wait a while for the container to start up
            time.sleep(10)
            # save the docker container id so we can stop it later
            global DOCKER_CONTAINER_ID
            DOCKER_CONTAINER_ID = p.stdout.decode("utf-8")
            print(f"Setting DOCKER_CONTAINER_ID to {DOCKER_CONTAINER_ID}")

    # move on with the rest of the setup
    print(
        "pytest_configure: start " + SQL_TEST_CONNECTION_STRING + " " + SQL_TEST_DBNAME
    )
    # create database so that we have tables ready
    create_database(SQL_TEST_CONNECTION_STRING, SQL_TEST_DBNAME)
    time.sleep(1)
    #    upload_synthetic_data.main(SQL_TEST_DBNAME)
    print("pytest_configure: end")


def pytest_unconfigure(config):
    """
    called before test process is exited.
    """

    print("pytest_unconfigure: start")
    # drops test db
    success, log = drop_db(SQL_TEST_CONNECTION_STRING, SQL_TEST_DBNAME)
    assert success, log
    # if we started a docker container in pytest_configure, kill it here.
    if DOCKER_CONTAINER_ID:
        print(f"Stopping docker container {DOCKER_CONTAINER_ID}")
        os.system("docker kill " + DOCKER_CONTAINER_ID)
    print("pytest_unconfigure: end")
