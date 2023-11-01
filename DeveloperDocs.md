## Running DTBase locally.

* We recommend that you use a fresh Python environment (either via virtualenv, conda, or poetry), and **Python version >=3.8 and <= 3.10.**

* Clone this repository and change to this directory.
* Install the `dtbase` package and dependencies (including the optional development dependencies) by running
```
pip install .[dev]
```
* Copy the file `.secrets/dtenv_template.sh` to `.secrets/dtenv.sh` if you will be using a cloud-based database, or `.secrets/dtenv_localdb.sh` if you will run a local postgres server using docker, and populate this file with values for the various environment variables (ask an existing developer for these).   Note that if using the docker option, you will need to have Docker installed and running on your machine.

### Running the backend API

The backend API is a flask app that provides REST API endpoints to facilitate reading and writing to the database.
* Navigate to the directory `dtbase/backend`.
* Run the command `./run.sh` if you will be using a cloud-based database, or `./run_localdb.sh` if you will be using a docker postgres container on your local machine.
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
