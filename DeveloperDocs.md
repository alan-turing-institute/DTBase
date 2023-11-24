## Installing DTBase

* We recommend that you use a fresh Python environment (either via virtualenv, conda, or poetry), and **Python version 3.10 <= and <=3.12.**

* Clone this repository and change to this directory.
* Install the `dtbase` package and dependencies (including the optional development dependencies) by running
```
pip install .[dev]
```

## Running an Instance of DTBase

DTBase has three main components:

- Postgresql Database
- Backend API
- Frontend API

All these components can be run either locally or deployed via Azure. The following sections contain instructions for running an instance of dtbase either locally or via Azure.

### Local Deployment

#### Running a Local Database

The postgresql database can be run via a locally deployed container with Docker.

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
export DT_SQL_PASS="password"
export DT_SQL_HOST="localhost"
export DT_SQL_PORT="5432"
export DT_SQL_DBNAME="dt_dev"
```
3. Run `source .secrets/dtenv_localdb.sh`
4. Install Docker
5. Install postgresql
6. Run a postgresql server in a docker container:

`docker run --name dt_dev -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgres`

7. To run the backend, we first need to create an empty database:

`createdb --host localhost --username postgres dt_dev`

#### Running the tests

1. Tests can now be run by locally by navigating into dtbase: `cd dtbase` and running the tests: `pytest tests`

#### Running the backend API

The backend API is a flask app that provides REST API endpoints to facilitate reading and writing to the database.
1. Navigate to the directory `dtbase/backend` and run the command `./run_localdb.sh`. You should then have the flask app listening on `http://localhost:5000` and be able to send HTTP requests to it.  See the [API docs](dtbase/backend/README.md) for details.
2. Optionally, you can use different modes for the backend, by running e.g.
   `DT_CONFIG_MODE=Debug ./run_localdb.sh` to run in debug mode. The valid
   options for `DT_CONFIG_MODE` can be found in `dtbase/backend/config.py`.

#### Running the frontend

The DTBase frontend is currently an extremely lightweight Flask webapp:
1. Install npm
2. Navigate to the directory `dtbase/webapp` and run the command `./run.sh`.
3. You should now be able to view the webapp on your browser at http://localhost:8000.
4. Like for the backend, you can use different modes for the frontend, by running e.g.
   `DT_CONFIG_MODE=No-login ./run.sh` to run with user login disabled. The valid
   options for `DT_CONFIG_MODE` for the frontend can be found in
   `dtbase/webapp/config.py`.


### Running with an Azure Deployed Database

1. Copy the file `.secrets/dtenv_template.sh` to `.secrets/dtenv.sh` and populate this file with values for the various environment variables (ask an existing developer for these). These environment variables will point towards an already existing database hosted on Azure.

#### Running the backend API

The backend API is a flask app that provides REST API endpoints to facilitate reading and writing to the database.

1. Your IP Address must be whitelisted on Azure. Ask one of the developers to help with this.
2. Navigate to the directory `dtbase/backend` and Run the command `./run.sh`.

You should then have the flask app listening on `http://localhost:5000` and be able to send HTTP requests to it.  See the [API docs](dtbase/backend/README.md) for details.

#### Running the frontend

Run the frontend in the same way as running locally.

## Contributing code

We run a set of linters and formatters on all code using [pre-commit](https://pre-commit.com/).
It is installed as a dev dependency when you run `pip install .[dev]`.
We recommend running `pre-commit install` so that pre-commit gets run every time you `git commit`, and only allows you to commit if the checks pass.
If you need to bypass such checks for some commit you can do so with `git commit --no-verify`.
