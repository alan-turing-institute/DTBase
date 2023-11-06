## Installing DTBase

* We recommend that you use a fresh Python environment (either via virtualenv, conda, or poetry), and **Python version >=3.8 and <= 3.10.**

* Clone this repository and change to this directory.
* Install the `dtbase` package and dependencies (including the optional development dependencies) by running
```
pip install .[dev]
```

## Running DTBase Locally

A version of DTBase can be run locally via Docker.

1. Copy the file `.secrets/dtenv_template.sh` to `.secrets/dtenv_localdb.sh`and populate this file with values for the various environment variables (ask an existing developer for these).
2. Install Docker.
3. Run a postgresql server in a docker container:

`docker run --name test_dtbase_db -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgres`

4. Tests can now be run by locally by navigating into dtbase: `cd dtbase` and running the tests: `pytest tests`

5. To run the backend locally, we can execute `./run_localdb.sh` . . .


## Running DTBase via the cloud

* Copy the file `.secrets/dtenv_template.sh` to `.secrets/dtenv.sh` and populate this file with values for the various environment variables (ask an existing developer for these).


### Running the backend API

The backend API is a flask app that provides REST API endpoints to facilitate reading and writing to the database.
* Navigate to the directory `dtbase/backend`.
* Run the command `./run.sh`
* You should then have the flask app listening on `http://localhost:5000` and be able to send HTTP requests to it.  See the [API docs](dtbase/backend/README.md) for details.

### Running the frontend

The DTBase frontend is currently an extremely lightweight Flask webapp.   To run this:
* Navigate to the directory `dtbase/webapp`.
* Set the environment variable `DT_BACKEND_URL` to point to the backend, i.e. if following the instructions above, do
```
export DT_BACKEND_URL=http://localhost:5000
```
* Execute the command `./run.sh`
* You should now be able to view the webapp on your browser at `http://localhost:8000`.

## Contributing code

We run a set of linters and formatters on all code using [pre-commit](https://pre-commit.com/).
It is installed as a dev dependency when you run `pip install .[dev]`.
We recommend running `pre-commit install` so that pre-commit gets run every time you `git commit`, and only allows you to commit if the checks pass.
If you need to bypass such checks for some commit you can do so with `git commit --no-verify`.
