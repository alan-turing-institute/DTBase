#!/usr/bin/env python

import os
import re
import subprocess
import time

from dtbase.core.constants import SQL_CONNECTION_STRING, SQL_DBNAME
from dtbase.core.db import connect_db, create_database, create_tables


def check_for_docker() -> str | bool:
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
    m = re.search(r"([0-9a-f]+)[\s]+postgres", output)
    if not m:
        return True  # Docker is running, but no postgres container
    else:
        return m.groups()[0]  # return the container ID


def start_docker_postgres() -> str | None:
    """
    Start a postgres docker container, if one isn't already running.

    Returns:
           container_id or None:  return int container_id if and only if we
                                  start a new docker container.
    """
    # see if docker is running, and if so, if postgres container exists
    docker_info = check_for_docker()
    if not docker_info:  # docker desktop not running at all
        print("Docker not found - will skip tests that use the database.")
        return
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
            container_id = p.stdout.decode("utf-8")
            return container_id


def create_db_tables() -> None:
    create_database(SQL_CONNECTION_STRING, SQL_DBNAME)
    engine = connect_db(SQL_CONNECTION_STRING, SQL_DBNAME)
    create_tables(engine)


def stop_docker_postgres(container_id: str) -> None:
    """
    Stop the docker container with the specified container_id
    """
    if container_id:
        print(f"Stopping docker container {container_id}")
        os.system("docker kill " + container_id)


def main() -> None:
    docker_check = check_for_docker()
    container_id = None
    if isinstance(docker_check, bool):
        if not docker_check:
            raise RuntimeError(
                "Looks like Docker isn't running - won't be able to start postgres "
                "server"
            )
        else:
            container_id = start_docker_postgres()
            print(f"Started postgres docker container with id {container_id}")
            create_db_tables()
    else:
        # don't need to do anything - container already running
        pass


if __name__ == "__main__":
    main()
