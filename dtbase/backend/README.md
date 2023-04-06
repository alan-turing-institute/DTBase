# API documentation

The DTBase backend is a Flask application providing an API for interacting with the database.
The endpoints in this document should be appended to a base url, which will depend on where you deploy the app.   If you are developing/running locally, it will be `http://localhost:5000`.   If you deploy to e.g. Azure, it will be somthing like `https://<your-azure-app-name>.azurewebsites.net`.



## Locations

Locations can be defined using any combination of floating point, integer, or string variables.   These variables, known as _LocationIdentifiers_ must be inserted into the database before an actual _Location_ can be entered.  The set of _LocationIdentifiers_ that is sufficient to define a _Location_ is called a _LocationSchema_.   A _Location_ will therefore have a _LocationSchema_, and one _LocationXYZValue_ for each _LocationIdentifier_ within that schema (where _XYZ_ can be "Float", "Integer" or "String").

The following endpoints are implemented:

### `/locations/insert_location_schema`
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
    - returns the payload, with status code 201


### `/locations/insert_location`
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
    (where the values should be in the same order as the identifiers).
    - returns status code 201, along with json:
    ```
    {
      "schema_name": <concatenation_of_identifier_names>,
      <identifier_name>: <value>,
      ...
    }
    ```


### `/locations/insert_location/<schema_name>`
* A POST request will add a new location, with a previously defined schema.
    - Payload should have the form
    ```
    {
      <identifier_name>: <value>,
      ...
    }
    ``` 
    for every identifier in the schema.
    - returns status code 201, along with the payload.


### `/location/list/<schema_name>`
* A GET request will list the Locations corresponding to the specified schema:
    - optionally filter by coordinates, if given payload of the form
    ```
    {"identifier_name": "value", ... }
    ```
    - returns `[{"id": <id:int> , <identifier_name:str>: <value>, ...}, ...]`


### `/location/list_location_schemas`
* A GET request will list all schemas:

    - returns
    ```
    [{"id": <id:int>, "name": <name:str>, "description":<description:str>,}, ...]
    ```

### `/location/list_location_identifiers`
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

### `/location/delete_location_schema/<schema_name>`
* A DELETE request will remove the schema with the specified name:
    - returns
    ```
      {
	"status": "success",
	"message": "Location schema <schema_name> has been deleted"
      }
     ```

### `/location/delete_location/<schema_name>`
* A DELETE request will remove the location with the specified schema name and values specified in the payload:

    - payload: `{<identifier:str> :<value>}, ...}`

    - returns
    ```
      {
	"status": "success",
	"message": "Location deleted successfully"
      }
     ```


## Sensors

The Sensor data model is as follows.   Every _Sensor_ has a _SensorType_ which in turn specifies the variable(s) it can measure - these are known as _SensorMeasures_.  Each _SensorMeasure_ specifies its datatype (float, int, string, or bool), and these are used to define the type of the corresponding _SensorXYZReadings_.   A _Sensor_ will also have a _SensorLocation_, which specifies a _Location_ as defined above, and a time window (possibly open-ended) when the sensor was at that location.

The endpoints are:

###
