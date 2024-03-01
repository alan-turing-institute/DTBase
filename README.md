# DTBase
A general base software package from which Digital Twins can be developed.

## Overview

### Goals of DTBase

The primary aim of DTBase is to provide a software package that developers can fork and use to deploy their own digital twin with minimal effort. This is an ambitious project as digital twins vary significantly and therefore DTBase needs to be both robust and flexible.
DTBase consists of three main parts: A PostgreSQL database, a backend app for interacting with the database and a frontend app for visuals. The database, backend and frontend communicate via restful APIs, therefore allowing users of DTBase to choose which components of the code base they require for their personal usecase.

We try to design the code base so as many of DTBase's features as possible can be deployed either locally or via Azure. There is no reason that DTBase couldn't be deployed on other cloud services, but Azure is what the developers have access to and therefore is the default service accomodated.

### Packages and technologies

* The core of DTBase is the database, for which we use PostgresSQL.
* The backend is written in Python, using the FastAPI and SQLAlchemy packages.
* The frontend is a Flask app written in Python.
* Continuous Integration and Continuous Deployment are done via Github Actions, which in turn build Docker images and push them to Dockerhub.
* Data ingress, Modelling and other services are implemented via Azure Functions.
* Scripted deployment on Azure is done via Pulumi.

We are prioritizing the implementation of the data model, and a backend API, as the first steps in DTBase.  Users should be able to interact with the database via REST API endpoints, to insert, delete, and retrieve data related to Locations, Sensors, and Predictive Models.

We also aim to include:
* Example ingress functions that retrieve data from an external API and use the DTBase API to store it in the database.
* An example of a predictive model (Arima) that makes use of sensor data.
* Pulumi scripts to deploy the full set of infrastructure on Microsoft Azure cloud.
* A very minimal frontend that will allow users to interact with some aspects of the API.

### API documentation

See [here](dtbase/backend/README.md) for a list of API endpoints, along with expected request and response structures.

### Deployment documentation

See [here](infrastructure/README.md) for docs on the Pulumi deployment.

### Developer documentation / Local running.

See [here](DeveloperDocs.md)

### History/The CROP project

The DTBase package is based on [CROP](https://github.com/alan-turing-institute/CROP), a Digital Twin for an underground farm, located in a disused air-raid shelter in Clapham, London. Some of the defining aspects of the CROP Digital Twin are:
* Ingress of real-time sensor data.
* Ingress of data from other sources (weather, power consumption, information specific to the farm).
* Predictive models run on a daily schedule to give predictions and uncertainties for future conditions.
* Database containing all historic environmental and crop data.
* Web frontend including:
  - Dashboard showing at-a-glance overview of conditions in the farm.
  - Straightforward method of displaying and downloading time-series from selected data sources.
  - Custom visualizations of various operational aspects.
  - Visualizations of the predictive model outputs, including interactive scenario selection.
  - Interactive 3D model of the farm.

All of this makes use of cloud-based infrastructure, and can be easily deployed on Microsoft Azure using Pulumi.

For DTBase, the aim is to replicate some (but not all) of the features of CROP, but generalizing as far as possible.  In particular:
* We make no assumptions on how *Locations* are defined in the digital twin.
* Rather than having separate database tables for each sensor type, we have a more flexible and general set of tables for *Sensors* and *Sensor Readings*.
* We follow the CROP model for defining the data structures around the predictive models, including model runs, the variables predicted in them, and the obtained values.
