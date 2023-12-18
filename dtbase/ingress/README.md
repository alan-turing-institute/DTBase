# Guide to data ingress in DTBase

This readme details how to write your own data ingress in DTBase using the ingress_weather as an example.

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

## get_data

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

For example, if we would like to return two different readings from a sensor, the output of `get_data` should look something like this:

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

## OpenWeatherMap Example

This section will now go through the OpenWeatherMap example in detail.
