# API documentation

The DTBase backend is a FastAPI application providing an API for interacting with the database.
This file used to list all the end points in the API.
That functionality has now been taken over by the backend docs page.
If you are developing/running locally, and your backend is running at `http://localhost:5000`, you can find the docs at `http://localhost:5000/docs`.
Correspondingly for an Azure deployment it will be something like `https://<your-azure-app-name>_backend.azurewebsites.net/docs`.
The docs are automatically generated from the code, and will list all the end points, the methods and payloads they accept, and what they return.

## Authentication

To be able to access any of the API end points you need an authentication token.
You can get one from the `/auth/login` endpoint using a username and a password.
Once you've obtained a token, you need to add it to header of any other API calls you make as a bearer token.
So if `/auth/login` returned
```
{
    "access_token": "abc"
    "refresh_token": "xyz"
}
```
then you would call the other end points with the following in the header of the request:
```
Authorization: Bearer abc
```

If your token expires, you can use the refresh token to get a new for some time still,
by calling the `/auth/refresh` end point. This one requires setting you header like above, but
using the refresh token (`xyz`) rather than the access token (`abc`).

## Locations

Locations can be defined using any combination of floating point, integer, or string variables.   These variables, known as _LocationIdentifiers_ must be inserted into the database before an actual _Location_ can be entered.  The set of _LocationIdentifiers_ that is sufficient to define a _Location_ is called a _LocationSchema_.   A _Location_ will therefore have a _LocationSchema_, and one _LocationXYZValue_ for each _LocationIdentifier_ within that schema (where _XYZ_ can be "Float", "Integer" or "String").

## Sensors

The Sensor data model is as follows.   Every _Sensor_ has a _SensorType_ which in turn specifies the variable(s) it can measure - these are known as _SensorMeasures_.  Each _SensorMeasure_ specifies its datatype (float, int, string, or bool), and these are used to define the type of the corresponding _SensorXYZReadings_.   A _Sensor_ may also have a _SensorLocation_, which specifies a _Location_ as defined above, and a time window (possibly open-ended) when the sensor was at that location.

## Models

TODO: Write a summary of how storing model data works.

## Users

TODO: Write a summary of how user management works.
