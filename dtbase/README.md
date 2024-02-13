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

## functions

Contains the required code to use services (ingress or models) in Azure Functions.

## services

This contains the base Classes for all services, including BaseService, BaseModel and BaseIngress. BaseModel and BaseIngress inherit from the BaseService Class.

## models

This is where the code for specific models is located. Instructions for how to write custom models can be found [here](models/README.md).

## Ingress

This is where code for specific data ingress is located. Data ingress is the act of pulling in data from another source such as an external API or database and inserting into the dtbase database via the backend. Instructions for how to write custom models can be found [here](ingress/README.md).
