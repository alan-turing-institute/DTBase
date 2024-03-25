# Running an Instance of DTBase

DTBase has three main components:

- PostgreSQL Database
- Backend API
- Frontend API

There are lots of different combinations of where each component is run. For instance, its possible to run the backend and frontend locally, but host the database somewhere else. This README will offer a number of suggestions of how to run the entire application stack.

We would recommend forking the entire repository and developing on that fork. Code changes to the repository will be inevitable.

## Summary

- [Managing Secrets and Environment Variables](#managing-secrets-and-environment-variables)
- [Run entire application stack locally via docker compose](#run-entire-application-via-docker-compose)
- [Installing DTBase](#installing-dtbase)
- [Running a local database](#running-a-local-database)
- [Running Tests](#running-the-tests)
- [Running the backend API Locally](#running-the-backend-api-locally)
- [Running the frontend locally](#running-the-frontend-locally)
- [Running with an Non-local Database](#running-with-an-non-local-database)
- [Running all components non-locally](#running-all-components-non-locally)
- [Contributing to code](#contributing-code)

## Managing Secrets and Environment Variables

DTBase makes use of a set of secret values, such as database passwords and encryption keys for logins. These are kept in the `.secrets` folder in a Bash shell script that sets environment variables with the secret values. For your own deployment you should

1. Copy the file `.secrets/dtenv_template.sh` to `.secrets/dtenv_localdb.sh`
2. Populate this file with following variables:
    ```
    #!/bin/bash

    # Test database
    export DT_SQL_TESTUSER="postgres"
    export DT_SQL_TESTPASS="password"
    export DT_SQL_TESTHOST="localhost"
    export DT_SQL_TESTPORT="5432"
    export DT_SQL_TESTDBNAME="test_db"

    # Dev database
    export DT_SQL_USER="postgres"
    export DT_SQL_PASS="<REPLACE_ME>"
    export DT_SQL_HOST="localhost"
    export DT_SQL_PORT="5432"
    export DT_SQL_DBNAME="dt_dev"

    export DT_DEFAULT_USER_PASS="<REPLACE_ME>"

    # Secrets for the web servers
    export DT_DEFAULT_USER_PASS="<REPLACE_ME>"
    export DT_FRONT_SECRET_KEY="<REPLACE_ME>"
    export DT_JWT_SECRET_KEY="<REPLACE_ME>"
    ```
    You should, of course, replace all the `<REPLACE_ME>` values with long strings of random characters, or other good passwords. They won't be need to be human-memorisable. If any of these values leak anyone can gain admin access to your DTBase deployment!

You can find more documentation about what each of the environment variables are for in `.secrets/dtenv_localdb.sh`.

In any terminal session where you want to e.g. run one of the web servers, you will need start out by

3. Activating the Python virtual environment you created.
4. Sourcing the secrets file, with `source .secrets/dtenv_localdb.sh`.

NOTE!: If running the application via Docker Compose, then this needs to be done in an .env file instead. Please follow the instructions [that section](#run-entire-application-via-docker-compose).

## Run Entire Application via Docker Compose

The easiest way to run all aspects of DTBase together is to use docker compose. The steps to do this is as follows:

1. Install Docker
2. We need to create an .env file for defining environment variables. Copy the `default.env` file and rename it `.env`. Replace the value that have `"<REPLACE_ME>"` in place.
3. `docker compose up -d` builds the images and then runs all the containers.

The backend and frontend are exposed at `http://localhost:5000/docs` and `http://localhost:8000` respectively. A volume is attached to the containers and will persist even after the containers have been stopped or deleted. The volume contains all the data from the database. If you want to start the application with a fresh database, then delete the volume before calling `docker compose` again.

This deployment is convenient for a quick local deployment. However, when changes are made to the code, the images need to be rebuilt. This doesn't take too long but isn't ideal. It's probabaly possible to tweak the dockerfile and compose files to mount the code so an image rebuild it not needed.

If you either don't want to spend time editing the docker setup, don't want to rebuild images each time a code change is made or simply want to avoid docker as much as possible, then move onto the next section.

## Installing DTBase

Running the seperate components locally via the command line requires DTBase to be installed as a package. Instructions are as follows:

1. We recommend that you use a fresh Python environment (either via virtualenv, conda, or poetry), and **Python version 3.10 <= and <=3.12.**
2. Clone this repository and change to this directory.
3. Install the `dtbase` package and dependencies (including the optional development dependencies) by running

```
pip install '.[dev]'
```

## Running a Local Database

The easiest way to run a PostgreSQL server locally is using a prebuilt Docker image.
1. Run `source .secrets/dtenv_localdb.sh`.
2. Install Docker
3. Install PostgreSQL
4. Run a PostgreSQL server in a Docker container:

    `docker run --name dt_dev -e POSTGRES_PASSWORD="<REPLACE_ME>" -p 5432:5432 -d postgres`

    The `"<REPLACE_ME>"` value here should be the one you set as `DT_SQL_PASS` in your `.secrets/dtenv_localdb.sh`.
5. Initialise the database:

    `createdb --host localhost --username postgres dt_dev`

If you've done this setup once and then e.g. rebooted your machine, all you should need to do is run `docker start dt_dev` to restart the existing Docker container.

## Running the tests

Assuming a local database has been setup, then the tests can now be run. The tests spin up its own backend and frontend applications automatically.

1. Tests can now be run by locally by running `python -m pytest`.

## Running the backend API Locally

The backend API is a FastAPI app that provides REST API endpoints for reading from and writing to the database. You can run it by:

1. Navigate to the directory `dtbase/backend` and run the command `./run_localdb.sh`. This starts the FastAPI app listening on `http://localhost:5000`. You can test it by sending requests to some of its endpoints using e.g. Postman or the `requests` library. To see all the API endpoints and what they do, navigate to `http://localhost:5000/docs` in a web browser.
2. Optionally, you can use different modes for the backend, by running e.g. `DT_CONFIG_MODE=Debug ./run_localdb.sh` to run in debug mode. The valid options for `DT_CONFIG_MODE` can be found in `dtbase/backend/config.py`.

## Running the frontend locally

The DTBase frontend is a Flask webapp. To run it you need to
1. Install npm (Node Package Manager)
2. In a new terminal session, again run `source .secrets/dtenv_localdb.sh`
3. Navigate to the directory `dtbase/frontend` and run the command `./run.sh`.
4. You should now be able to view the frontend on your browser at `http://localhost:8000`.
5. You can log in with the username `default_user@localhost` and the password you set as `DT_DEFAULT_USER_PASS` above when you created `dtenv_localdb.sh`.
6. Like for the backend, you can use different modes for the frontend, by running e.g. `DT_CONFIG_MODE=Auto-login ./run.sh` to be always automatically logged in as the default user. The valid options for `DT_CONFIG_MODE` for the frontend can be found in `dtbase/frontend/config.py`.

A tip: When developing the frontend, it can be very handy to run it with `FLASK_DEBUG=true DT_CONFIG_MODE=Auto-login ./run.sh`. The first environment variable makes it such that Flask restarts every time you make a change to the code. (The backend already by default has a similar autorefresh option enabled.) The second one makes Flask automatically log in as the default user. This way when you make code changes, you can see the effect immediately in your browser without having to restart and/or log in.

## Running with an Non-local Database

Sometimes you want to run the backend and the frontend locally, but have the database reside elsewhere, e.g. on Azure. To do this,
1. Copy the file `.secrets/dtenv_template.sh` to `.secrets/dtenv.sh` and populate this file with values for the various environment variables. These are mostly the same as above when running a local database, except for `DT_SQL_HOST`, `DT_SQL_PORT`, `DT_SQL_USER`, and `DT_SQL_PASS`. These should be set to match the hostname, port, username, and password for the PostgreSQL server, where ever it is running. If you want to run against a database on Azure deployed by Pulumi, you may want to consult your Pulumi config for e.g. the password.

To run the backend with this new set of environment variables, go to `dtbase/backend` and run `./run.sh`. The frontend can be run exactly the same way as when your database is local.

Note that you may need to whitelist your IP address on the PostgreSQL server for it to accept your connection. This is necessary when the database is hosted on Azure, for instance.

## Running all components non-locally

Please refer to the [infrastructure readme](../infrastructure/README.md) for documentation of how to deploy the entire application stack on Azure. There is no reason this application couldn't be deployed on other platforms but we don't offer any instructions of how to do this.

## Contributing code

We run a set of linters and formatters on all code using [pre-commit](https://pre-commit.com/). It is installed as a dev dependency when you run `pip install .[dev]`. You also need to make sure you've run `npm install --prefix dtbase/frontend/ --include=dev ` to install the linters and formatters for the frontend code. We recommend running `pre-commit install` so that pre-commit gets run every time you `git commit`, and only allows you to commit if the checks pass. If you need to bypass such checks for some commit you can do so with `git commit --no-verify`.

We recommend reading the [docs.md](docs.md) file to gain an understanding of what the various parts of the codebase do and how they work.
