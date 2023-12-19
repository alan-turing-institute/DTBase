# Guide to data ingress in DTBase

This readme details how to write your own data ingress in DTBase using the OpenWeatherMap as an example.

## BaseIngress

The BaseIngress Class has all the general purpose tools for interacting with the backend (and TODO: Azure Functions).
For a custom data ingress, the user should create their own custom DataIngressClass inheriting from the BaseIngress Class.
For example:

```
class CustomDataIngress(BaseIngress):
    """
    Custom class inheriting from the BaseIngress class for interacting with the OpenWeatherData API.
    """

    def __init__(self) -> None:
        super().__init__()
```

### Method: get_data

The user then needs to write a `get_data` method in the `CustomDataIngress`. This method should extract data from a source (could be an online API or from disk or anywhere) and return the data:

```
def get_data():
    api_url = 'example/online/api/endpoint'
    data = request.get(api_url)
    return data
```

The structure of the data should be as follows:

```
[(endpoint, payload), (endpoint, payload), etc.]
```

The payload should be in a very specific format depending on which DTBase backend endpoint you wish to post the data to. The documentation for all available backend endpoints can be found in the [backend README.md](..//backend/README.md).

For example, if we would like to insert two different sensor readings, then the output of `get_data` should look something like this:

```
[
    '/sensor/insert-sensor-readings', {
  "measure_name": <measure_name1:str>,
  "unique_identifier": <sensor_unique_identifier:str>,
  "readings": <list of readings>,
  "timestamps": <list of timestamps in ISO 8601 format '%Y-%m-%dT%H:%M:%S'>
},
    '/sensor/insert-sensor-readings', {
  "measure_name": <measure_name2:str>,
  "unique_identifier": <sensor_unique_identifier:str>,
  "readings": <list of readings>,
  "timestamps": <list of timestamps in ISO 8601 format '%Y-%m-%dT%H:%M:%S'>
}
]
```

### Method: ingress_data

The `ingress_data` method is used to send data to the database via DTBase's backend. The user doesn't need to write this, but this is the method to call after defining `get_data`.

1. Runs the `get_data` method to extract data from a source
2. logs into the backend
3. Loops through the data `get_data` returns and posts it to the backend.


## OpenWeatherMap Example

This section will now go through the [ingress_weather](ingress_weather.py) example in detail.

The goal of the weather ingress is to extract data from the OpenWeatherData API and enter it into our database via the backend.There are two different APIs depending on whether the user wants historical data or forecasting.

### 1. Define Payloads

3 Constants are defined at the top of ingress_weather.py:

- *SENSOR_TYPE:* Define the sensor type as detailed by the "/sensor/insert-sensor-type" API endpoint.
- *SENSOR_OPENWEATHERMAPHISTORICAL*: Define the sensor as detailed by the "/sensor/insert-sensor" API endpoint. This sensor is for the historical data API.
- *SENSOR_OPENWEATHERMAPFORECAST*: Same as previous sensor but for forecasting.

These constants are dictionaries and define the sensor type and sensor payloads. The payload for entering sensor-readings is built in the get_data method.

### 2. OpenWeatherDataIngress

We then write a custom class that inherits from BaseIngress. There are a number of _* methods that are used to handle different combinations of start and end dates given by the user. A lot of this complexity comes from their being two different APIs.

The important method is the `get_data`. This method takes in `from_dt` and `to_dt` arguments to define when the user wants to extract information from the API. There is then some specific preprocessing to get the exact data we want from the API.

Finally, we return data in a very specific format:

```
sensor_type_output = [("/sensor/insert-sensor-type", SENSOR_TYPE)]

sensor_output = [("/sensor/insert-sensor", sensor_payload)]

sensor_readings_output = [
            ("/sensor/insert-sensor-readings", payload) for payload in measure_payloads
        ]

return sensor_type_output + sensor_output + sensor_readings_output
```

**The get_data method MUST returns a list of tuples structures as (endpoint, payload) for the ingress method to integrate into the rest of DTBase.**

### 3. Uploading data to database

After writing your own custom get_data method, we can then send it to the database via the dtbase backend. This is simply done by calling

```
weather_ingress = OpenWeatherDataIngress()
weather_ingress.ingress_data(dt_from, dt_to)
```

Under the hood, the class finds the get_data method, runs the get_data method, and then calls the backend API to upload the data to the database. It handles authentication and error handling. This method uses any input arguments required in get_data.

**Note: It uses environment variables for API keys and authentication so ensure you have the correct variables set.**

The `example_weather_ingress` function shows how to use this code to ingress weather data.
