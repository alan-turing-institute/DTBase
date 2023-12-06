# API documentation

The DTBase backend is a Flask application providing an API for interacting with the database.
The endpoints in this document should be appended to a base url, which will depend on where you deploy the app.   If you are developing/running locally, it will be `http://localhost:5000`.   If you deploy to e.g. Azure, it will be somthing like `https://<your-azure-app-name>.azurewebsites.net`.


## Authentication

To be able to access any of the API end points you need an authentication token. You can get it from the following endpoint:

### `/auth/login`
* A POST request will return an authentication token
    - Payload should have the form
    ```
    {
      "email": <email:str>,
      "password": <password:str>
    }
    ```
    - returns a payload of the form
    ```
    {
        "access_token": <token_value:str>
        "refresh_token": <token_value:str>
    }
    ```
    with status code 200.

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
by calling the below end point. This one requires setting you header like above, but
using the refresh token (`xyz`) rather than the access token (`abc`).
If your refresh token expires too you will have to log in again.

### `/auth/refresh`
* A POST request will return an authentication token
    - No payload needed, just the authorization header.
    - returns a payload of the form
    ```
    {
        "access_token": <token_value:str>
        "refresh_token": <token_value:str>
    }
    ```
    with status code 200.

## User management

Users are identified by their email address and authenticated with a password.
The following endpoints are implemented:

### `/user/create-user`
* A POST request will add a new user.
    - Payload should have the form
    ```
    {
      "email": <schema_email:str>,
      "password": <schema_password:str>
    }
    ```
    - Returns with status code 201


### `/user/delete-user`
* A DELETE request will delete a user.
    - Payload should have the form
    ```
    {
      "email": <schema_email:str>,
    }
    ```
    - Returns with status code 200

### `/user/change-password`
* A POST request will change the password of a user.
    - Payload should have the form
    ```
    {
      "email": <schema_email:str>,
      "password": <schema_password:str>
    }
    ```
    where the password is the new password.
    - Returns with status code 200

### `/user/list-users`
* A GET request list all existing users by email.
    - No payload needed.
    - Returns 200 with
    ```
    [ email_of_user_1, email_of user2, ... ]
    ```


## Locations

Locations can be defined using any combination of floating point, integer, or string variables.   These variables, known as _LocationIdentifiers_ must be inserted into the database before an actual _Location_ can be entered.  The set of _LocationIdentifiers_ that is sufficient to define a _Location_ is called a _LocationSchema_.   A _Location_ will therefore have a _LocationSchema_, and one _LocationXYZValue_ for each _LocationIdentifier_ within that schema (where _XYZ_ can be "Float", "Integer" or "String").

The following endpoints are implemented:

### `/location/insert-location-schema`
* A POST request will add a new location schema and its identifying variables.
    - Payload should have the form
    ```
    {
      "name": <schema_name:str>,
      "description": <schema_description:str>
      "identifiers": [
                 {"name":<name:str>, "units":<units:str>,"datatype":<datatype:str>},
                 ...
                    ]
    }
    ```
    where "datatype" must be one of "string", "integer", "float", "boolean".
    - returns status code
        - 201 on success
        - 409 if a schema with this name exists already


### `/location/insert-location`
* A POST request will add a new location, with a schema and its identifying variables.
The schema name will be a concatenation of the identifier names.
    - Payload should have the form:
    ```
    {
      "identifiers": [
                 {"name":<name:str>, "units":<units:str>,"datatype":<datatype:str>},
                 ...
                    ],
      "values": [<val1>, ...]
    }
    ```
    (where the values should be in the same order as the identifiers) and "datatype" must be one of "string", "integer", "float", "boolean".
    - returns status code
        - 201 on success
        - 409 if the location exists already
    - on success the return payload will also include a `schema_name` field.


### `/location/insert-location-for-schema`
* A POST request will add a new location, with a previously defined schema.
    - Payload should have the form
    ```
    {
      "schema_name": <schema_name:str>,
      <identifier_name>: <value:float|int|str|bool>,
      ...
    }
    ```
    with an identifier name and value for every identifier in the schema.
    - returns status code
        - 201 on success
        - 400 if the location schema does not exist
        - 409 if the location exists already


### `/location/list-locations`
* A GET request will list the Locations corresponding to the specified schema:
    - optionally filter by coordinates, if given identifiers in the payload,
      which should be of the form
    ```
    {
       "schema_name" : <schema_name:str>,
       "<identifier_name>": <value:float|int|str|bool>,
        ...
    }
    ```
    - returns `[{"id": <id:int> , <identifier_name:str>: <value>, ...}, ...]`


### `/location/list-location-schemas`
* A GET request will list all schemas:
    - returns
    ```
    [{"id": <id:int>, "name": <name:str>, "description":<description:str>,}, ...]
    ```

### `/location/list-location-identifiers`
* A GET request will list all identifiers:
    - returns
    ```
    [
      {
	"id": <id:int>,
	"name": <name:str>,
	"datatype":<datatype:str>,
	"units":<units:str>,
      },
      ...
    ]
    ```

### `/location/get-schema-details`
* A GET request to get all information, including identifiers, for a location schema:

    - payload should be
    ```
    {
      "schema_name": <schema_name:str>
    }
    ```
    - returns 400 if schema name isn't valid, otherwise status code 200 with
    ```
    {
      "id": <id:int>,
      "name": <name:str>,
      "description": <description:str>,
      "identifiers": [
        {
	      "id": <id:int>,
	      "name": <name:str>,
	      "datatype": <datatype:str>,
	      "units": <units:str>,
        },
        ...
      ]
    }
    ```

### `/location/delete-location-schema`
* A DELETE request will remove the schema with the specified name.
    - payload should contain:
    ```
    {"schema_name": <schema_name:str>}
    ```
    - returns status code
        - 200 on success
        - 400 if schema does not exist

### `/location/delete-location`
* A DELETE request will remove the location with the specified schema name and values specified in the payload:
    - payload:
    ```
    {
       "schema_name" : <schema_name:str>,
        <identifier_name:str>: <value:float|int|str|bool>,
        ...
    }
    ```
    - returns status code
        - 200 on success
        - 400 if schema does not exist


## Sensors

The Sensor data model is as follows.   Every _Sensor_ has a _SensorType_ which in turn specifies the variable(s) it can measure - these are known as _SensorMeasures_.  Each _SensorMeasure_ specifies its datatype (float, int, string, or bool), and these are used to define the type of the corresponding _SensorXYZReadings_.   A _Sensor_ will also have a _SensorLocation_, which specifies a _Location_ as defined above, and a time window (possibly open-ended) when the sensor was at that location.

The endpoints are:

### `/sensor/insert-sensor-type`
* A POST request, will add a new sensor type.
    - Payload should have the form
    ```
    {
      "name": <type_name:str>,
      "description": <type_description:str>
      "measures": [
                 {"name":<name:str>, "units":<units:str>,"datatype":<datatype:str>},
                 ...
                    ]
    }
    ```
    where "datatype" must be one of "string", "integer", "float", "boolean".

    - returns status code 201, alongside the payload.

### `/sensor/insert-sensor`
* A POST request, will add a new sensor for an existing sensor type.
    - Payload should have the form
    ```
    {
      "type_name": <sensor_type_name:str>,
      "unique_identifier": <unique identifier:str>,
    }
    ```
    by which the sensor will be distinguished from all others, and optionally
    ```
    {
      "name": <human readable name:str>,
      "notes": <human readable notes:str>
    }
    ```
    - returns status code 201, alongside the payload.

### `/sensor/insert-sensor-location`
* A POST request, will add a new sensor location.
    - Payload should have the form
    ```
    {
      "unique_identifier": <unique identifier of the sensor:str>,
      "location_schema": <name of the location schema to use:str>,
      "coordinates": <coordinates to the location:dict>
    }
    where the coordinates dict is keyed by location identifiers.
    ```
    and optionally also
    ```
    {
      "installation_datetime": <date from which the sensor has been at this location:str>
    }
    ```
    If no installation date is given, it's assumed to be now.

    - returns status code 201, alongside the payload.

### `/sensor/list-sensor-locations`
* A GET request, will list the location history of a sensor.
    - Payload should specify the id of the sensor in the form
    ```
    {
      "unique_identifier": <unique identifier of the sensor:str>,
    }
    ```
    - returns status code 200, alongside results of form
    ```
    [
        {"id": <id:int>, "installation_datetime": <installation_datetime:datetime>, "location_identifer": <location_identifier:identifier_type>, ...},
        ...
    ]
    ```

### `/sensor/insert-sensor-readings`
* A POST request, will add a sensor reading for a given sensor for a given measure.
    - Payload should have the form
    ```
    {
      "measure_name": <measure_name:str>,
      "unique_identifier": <sensor_unique_identifier:str>,
      "readings": <list of readings>,
      "timestamps": <list of timestamps in ISO 8601 format '%Y-%m-%dT%H:%M:%S'>
    }
    ```

    - returns status code 201, alongside the payload.

### `/sensor/list-sensors`
* A GET request, will list all sensors.
    - Optionally, to filter by type name, include payload of the form
    ```
    {
      "type_name": <sensor_type_name:str>,
    }
    ```
    - returns status code 200, alongside results of all sensors in the form
    ```
    [
        {
            "id": <id:int>,
            "name": <name:str>,
            "notes": <notes:str>,
            "sensor_type_id": <sensor_type_id:int>,
            "sensor_type_name": <sensor_type_name:str>,
            "unique_identifier": <unique_identifier:str>
        },
        ...
    ]
    ```

### `/sensor/list-sensor-types`
* A GET request, will list all sensor types.
    - returns status code 200, alongside results in the form
    ```
    [
        {
            "description": <description:str>,
            "id": <id:int>,
            "measures": [
                {"datatype": <datatype:str>, "name": <name:str>, "units": <units:str>},
                ...
                ],
            "name": <name:str>
        },
        ...
    ]
    ```

### `/sensor/list-measures`
* A GET request, will list all defined sensor measures.
    - returns status code 200, alongside results in the form
    ```
    [
        {"datatype": <datatype:str>, "id": <id:int>, "name": <name:str>, "units": <units:str>},
        ...
    ]
    ```

### `/sensor/sensor-readings`
* A GET request, will list all readings between two timestamps for a specified sensor for a specified measure. Each timestamp (datetime) is specified in ISO format (i.e., %Y-%m-%dT%H:%M:%S)
    - Payload should have the form
    ```
    {
        measure_name: <measure_name:str>,
        unique_identifier: <sensor_uniq_id:str>,
        dt_from: <dt_from:str>,
        dt_to: <dt_to:str>
    }
    ```

    - returns:
      if unsuccessful due to wrong date time format, status code 400 is returned.
      else, it returns status code 200, alongside results in the form.
    ```
    [
        {"timestamp": <timestamp:str>, "value": <value:integer|float|string|boolean>},
        ...
    ]
    ```

### `/sensor/delete-sensor`
* A DELETE request, will delete a sensor.
    - Payload should have the form
    ```
    {
        unique_identifier: <sensor_uniq_id:str>
    }
    ```
    - returns status code 200, alongside message in the form
    ```
    {"message": "Sensor deleted"}
    ```

### `/sensor/delete-sensor-type`
* A DELETE request, will delete a sensor type.
    - Payload should have the form
    ```
    {
        type_name: <sensor_type_name:str>
    }
    ```
    - returns status code 200, alongside message in the form
    ```
    {"message": "Sensor type deleted"}
    ```

## Models

API endpoints for the models is as follows.

### `/model/insert-model`
* A POST request, will add a model.
    - Payload should have the form
    ```
    {
        "name": <model_name:str>
    }
    ```

    - returns status code 201, alongside the payload.

### `/model/list-models`
* A GET request, will list all models.
    - returns status code 200, alongside result in the form:
    ```
    [
        {"id": <id:int>, "name": <name:str>},
        ...
    ]
    ```

### `/model/delete-model`
* A DELETE request, will remove a model with the specified name.
    - Payload should have the form
    ```
    {
        "name": <model_name:str>
    }
    ```

    - returns status code 200, alongside message:
    ```
    {"message": "Model deleted."}
    ```

### `/model/insert-model-scenario`
* A POST request, will add a model scenario for a given model.
    - Payload should have the form
    ```
    {
        "model_name": <model_name:str>,
        "description": <description:str|None|null>,
    }
    ```

    - returns status code 201, alongside the payload.

### `/model/list-model-scenarios`
* A GET request, will list all model scenarios.
    - returns status code 200, alongside result in the form:
    ```
    [
        {"id": <id:int>, "model_id": <model_id:int>, "description": <description:str|None|null>},
        ...
    ]
    ```

### `/model/delete-model-scenario`
* A DELETE request, will remove a model scenario with the specified model name.
    - Payload should have the form
    ```
    {
        "model_name": <model_name:str>,
        "description": <description:str>
    }
    ```

    - returns status code 200, alongside message:
    ```
    {"message": "Model scenario deleted."}
    ```

### `/model/insert-model-measure`
* A POST request, will add a new model measure.'
    - Payload should have the form
    ```
    {
        "name": <name of this measure:str>
        "units": <units in which this measure is specified:str>
        "datatype": <value type of this model measure:str>
    }
    ```
    where "datatype" must be one of "string", "integer", "float", "boolean".

    - returns status code 201, alongside the payload.


### `/model/list-model-measures`
* A GET request, will list all model measures.
    - returns status code 200, alongside result in the form:
    ```
    [
        {
            "id": <id:int>,
            "name": <name:str>,
            "units": <units:str>,
            "datatype": <datatype:str>
        },
        ...
    ]
    ```

### `/model/delete-model-measure`
* A DELETE request, will remove a model measure with the specified measure name.
    - Payload should have the form
    ```
    {"name": <name:str>}
    ```

    - returns status code 200, alongside message:
    ```
    {"message": "Model measure deleted"}
    ```

### `/model/insert-model-run`
* A POST request, will add a model run.
    - Payload should have the form
    ```
    {
        "model_name": <name of the model that was run:str>
        "scenario_description": <description of the scenario:str>
        "measures_and_values": <results of the run:list of dicts with the below keys>
            "measure_name": <name of the measure reported:str>
            "values": <values that the model outputs:list>
            "timestamps": <timestamps associated with the values:list>
    }
    ```
    Optionally the following can also be included in the paylod
    ```
    {
        "time_created": <time when this run was run, `now` by default:string>
        "create_scenario": <create the scenario if it doesn't already exist, False by
                            default:boolean>
    }
    ```

    - returns status code 201, alongside the payload.


### `/model/list-model-runs`
* A GET request, will list all model runs.
    - Payload should have the form
    ```
    {
        "model_name": <name of the model to get runs for:str>,
        "dt_from": <datetime string for earliest readings to get (inclusive):str>,
        "dt_to": <datetime string for last readings to get (inclusive):str>,
        "scenario": <scenario:str> (optional, by default all scenarios),
    }
    ```
    datetime in dt_from and dt_to should be specified in the ISO 8601 format: '%Y-%m-%dT%H:%M:%S.

    - returns status code 200, alongside result in the form:
    ```
    [
        {
            "id": <id:int>,
            "model_id": <model_id:int>,
            "model_name": <model_name:str>,
            "scenario_description": <scenario_description:str>,
            "scenario_id": <scenario_id:int>,
            "time_created": <time_created:datetime_string>
        },
        ...
    ]
    ```

### `/model/get-model-run-sensor-measure`
* A GET request, will get the corresponding sensor_id and measure for a given model run.
    - Payload should have the form
    ```
    {
        run_id: <run_id:int> (id of the model run),

    }
    ```

    - returns status code 200, alongside result in the form:
    ```
    {
       "sensor_unique_id": <sensor_unique_id:str>,
       "measure_name": <measure_name:str>
    }
    ```

### `/model/get-model-run`
* A GET request, will get the output of a model run for a given model measure.
    - Payload should have the form
    ```
    {
        run_id: <run_id:int> (id of the model run),
        measure_name: <measure_name:str>,
    }
    ```

    - returns status code 200, alongside result in the form:
    ```
    [
        {
            "timestamp": <timestamp:str>,
            "value": <value:integer|float|string|boolean>
        },
        ...
    ]
    ```
    timestamp string is specified in ISO 8601 format: '%Y-%m-%dT%H:%M:%S.
