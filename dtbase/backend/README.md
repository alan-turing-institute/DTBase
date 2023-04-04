## API documentation

The DTBase backend is a Flask application providing an API for interacting with the database.
The endpoints in this document should be appended to a base url, which will depend on where you deploy the app.   If you are developing/running locally, it will be `http://localhost:8000`.   If you deploy to e.g. Azure, it will be somthing like `https://<your-azure-app-name>.azurewebsites.net`.

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
    - Payload should have the form
    ```
    {
      "identifiers": [
                 {"name":<name:str>, "units":<units:str>,"datatype":<datatype:str>},
                 ...
                    ],
      "values": [<val1>, ...]
    }

    ``` (where the values should be in the same order as the identifiers).
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

    ``` for every identifier in the schema.
    - returns status code 201, along with the payload


### `/locations/list/<schema_name>`
* A GET request will list the Locations corresponding to the specified schema:
    - optionally filter by coordinates, if given payload of the form
    ```
    {"identifier_name": "value", ... }
    ```
    - returns `[{name: , }, ...]`
