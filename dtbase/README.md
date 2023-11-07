# the `dtbase` package

This directory contains the Python package called `dtbase` that is installed if you do `pip install .` from the directory above this one, i.e. after doing that, you should be able to open a python session from anywhere and do `import dtbase`.

There are a few importand subdirectories within this package:

## core

This contains:
* The database schema (in `structure.py`)
* Various common utilities to interact with the database (in `utils.py`)
* Functions to insert and retrieve data from the database (in `queries.py`, `models.py`, `locations.py`, `sensors.py`)

## backend

This is a Flask application, providing API endpoints for interacting with the database (via the core functions).
The endpoints are grouped into `location`, `model`, and `sensor`, and within each there is a file `routes.py` defining the methods and URLs.

## webapp

This is another Flask application, providing a basic web interface.   This will send and receive HTTP requests to and from the backend, allowing users to insert sensors, locations etc. to the database, and to view time-series plots or data tables.
The frontend pages are grouped into `locations`, `models`, and `sensors` and within each there is a `routes.py` file and at least one `templates/xyz.html` file defining the URLs and the content to be displayed.  There is also Javascript code in `base/static/javascript` that contains code for making plots and tables.

## models

This is where the code for predictive models goes.   Common code for retrieving and cleaning training data is located in the `utils/dataprocessor` directory.

## ingress

This is where code to retrieve data from e.g. external APIs will live.   The scripts here will retrieve such data and use the backend API endpoints to insert it into the database.
