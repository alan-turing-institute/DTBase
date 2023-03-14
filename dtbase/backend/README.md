## API documentation

The DTBase backend is a Flask application providing an API for interacting with the database.
The endpoints in this document should be appended to a base url, which will depend on where you deploy the app.   If you are developing/running locally, it will be `http://localhost:8000`.   If you deploy to e.g. Azure, it will be somthing like `https://<your-azure-app-name>.azurewebsites.net`.

The following endpoints are implemented:

### `/locations/list/<schema_name>`
* A GET request will list the Locations corresponding to the specified schema:
    - optionally filter by coordinates, if given payload of the form
    ```
    {"identifier_name": "value", ... }
    ```
    - returns `[{name: , }, ...]`
