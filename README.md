# DTBase
A starting point from which digital twins can be developed.

### What DTBase is and isn't

DTBase aims to be a software package that developers can fork and use to develop their own digital twin with minimal effort.
Digital twins mean quite different things to different people, and thus we should clarify.
DTBase has
* A relational database, for holding both observational data (from e.g. sensors) and computational data (from models).
* A web server that wraps the database in a REST API. A user should never directly interact with the database, but rather through the API.
* A frontend web server, that provides a barebones graphical web user interface.
* An infrastructure-as-code configuration for deploying these resources on Azure.
* Tools for implementing your own "services", as DTBase calls them: Snippets of code that run periodically or on demand and interact with the backend API, such as data ingress functions or forecasting models.
* A few example services:
    * One to ingress weather data from OpenWeatherMap
    * One for running the Arima time series forecasting model
* Basic access control (user accounts and logins).

Some things DTBase does not, currently, have:
* Anything related to physical 3D structure of the objects that it is twinning. We have a very basic system for tracking locations in the twin, and for instance assigning sensors to locations, but this remains underdeveloped.
* Comprehensive visualisation tools. The frontend has basic time series plotting capabilities, but that's it.
* Sophisticated model orchestration. The services infrastructure can be used to store parameters for models and run them on demand, but the rest remains in development.
* Anything for using the digital twin to control the real asset.

DTBase may not be for you if
* Your idea of digital twin centres a CAD or Unity model of the thing being twinned.
* You need a plug-and-play, ready made software package that you `pip install` and run.

DTBase may be for you if
* Your idea of digital twin starts centres around a single data store, running models, and visualising data and model results from various sources.
* You want a codebase you can use as a starting point, and are willing to develop more bespoke features on top of it.

You may choose to only use parts of the infrastructure that DTBase offers.
For instance, the frontend doesn't offer any functionality that the backend API doesn't have, so you can only use the backend, and develop your own frontend from scratch.
We have designed the codebase so that as many of DTBase's features as possible can be deployed either locally or via Azure.
There is no reason that DTBase couldn't be deployed on other cloud services, but Azure is what we provide an infrastructure-as-code configuration for.

### Tech stack

* Most of the code is Python, except for browser stuff which is in Typescript and Jinja templates.
* The relational database is PostgresSQL.
* The backend is written in Python, using the FastAPI and SQLAlchemy packages.
* The frontend is a Flask app written in Python.
* Continuous Integration and Continuous Deployment are done via Github Actions, which in turn build Docker images and push them to Dockerhub.
* Infrastructure-as-code configuration is done using Pulumi.
* The example services (weather ingress, Arima) are implemented as Azure Functions.

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
