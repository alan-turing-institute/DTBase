# DTBase
A general base package from which Digital Twins can be developed.

## Overview

### History/The CROP project

The DTBase package is based on [CROP](https://github.com/alan-turing-institute/CROP), a Digital Twin for an underground farm, in a disused air-raid shelter in Clapham, London.   Some of the defining aspects of the CROP Digital Twin are:
* Ingress of real-time sensor data.
* Ingress of data from other sources (weather, power consumption, information specific to the farm).
* Predictive models run on a daily schedule to give predictions and uncertainties for future conditions.
* *Database*.
* Web frontend including:
 - Dashboard showing at-a-glance overview of conditions in the farm.
 - Straightforward method of displaying and downloading time-series from selected data sources.
 - Custom visualizations of various operational aspects.
 - Interactive 3D model of the farm.

All of this makes use of cloud-based infrastructure, and can be easily deployed on Microsoft Azure using Pulumi.

### Goals of DTBase

For DTBase, the aim is to replicate some (but not all) of the features of CROP, but generalizing as far as possible.  In particular:
* We make no assumptions on how *Locations* are defined in the digital twin.
* Rather than having separate database tables for each sensor type, we have a more flexible and general set of tables for *Sensors* and *Sensor Readings*.
* We follow the CROP model for defining the data structures around the predictive models, including model runs, the variables predicted in them, and the obtained values.

We are prioritizing the implementation of the data model, and a backend API, as the first steps in DTBase.  Users should be able to interact with the database via REST API endpoints, to insert, delete, and retrieve data related to Locations, Sensors, and Predictive Models.

We also aim to include:
* Example ingress functions that retrieve data from an external API and use the DTBase API to store it in the database.
* An example of a predictive model (Arima) that makes use of sensor data.
* Pulumi scripts to deploy the full set of infrastructure on Microsoft Azure cloud.
* A very minimal frontend that will allow users to interact with some aspects of the API.

### Packages and technologies

* The core of DTBase is the database, for which we use PostgresSQL.
* The backend is written in Python, using the Flask and SQLAlchemy packages.
* Continuous Integration and Continuous Deployment is done via Github Actions, which in turn build Docker images and push them to Dockerhub.
* The data ingress, and the scheduled running of the predictive model, is done via Azure Functions.
* Scripted deployment makes use of Pulumi.

### API documentation

See [here](backend/README.md) for a list of API endpoints, along with expected request and response structures.


### Deployment documentation

See [here](infrastructure/README.md) for docs on the Pulumi deployment.

### Developer documentation / Local running.

See [here](DeveloperDocs.md)

### Contributing

See [here](Contributing.md)