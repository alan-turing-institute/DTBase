"""
Python module to import data using the Openweathermap API
"""
import os
import json
import logging
import requests

# co-ordinates of Clapham farm
LAT = 51.45
LON = 0.14
OPENWEATHERMAP_HISTORY_URL = (
    "https://api.openweathermap.org/data/2.5/onecall/timemachine?"
    f"lat={LAT}&lon={LON}&units=metric&appid="
)
OPENWEATHERMAP_FORECAST_URL = (
    f"https://api.openweathermap.org/data/3.0/onecall?"
    f"lat={LAT}&lon={LON}&units=metric&appid="
)
BACKEND_URL = os.environ["DT_BACKEND_URL"]


# Mapping of Openweathermap metrics to sensor measures in the database.
METRICS_TO_MEASURES = {
    "temp": {
        "name": "temperature",
        "units": "degrees Celsius",
    },
    "humidity": {
        "name": "relative humidity",
        "units": "percent",
    },
    "pressure": {
        "name": "air pressure",
        "units": "millibar",
    },
    "wind_speed": {
        "name": "wind speed",
        "units": "m/s",
    },
    "wind_deg": {
        "name": "wind direction",
        "units": "degrees",
    },
    "rain": {
        "name": "rainfall",
        "units": "mms",
    },
}

# Sensor types that Hyper reports data for
SENSOR_TYPES = [
    {
        "name": "weather",
        "description": "Weather-related measurements",
        "measures": [
            {
                "name": "temperature",
                "units": "degrees Celsius",
                "datatype": "float",
            },
            {
                "name": "relative humidity",
                "units": "percent",
                "datatype": "float",
            },
            {
                "name": "air pressure",
                "units": "millibar",
                "datatype": "float",
            },
            {
                "name": "wind speed",
                "units": "m/s",
                "datatype": "float",
            },
            {
                "name": "wind direction",
                "units": "degrees",
                "datatype": "float",
            },
            {
                "name": "rain",
                "units": "mm",
                "datatype": "float",
            },
        ],
    },
]


# Mapping of sensor IDs to their types
SENSORS = {
    "OpenWeatherMapHistory": {"type": "weather"},
    "OpenWeatherMapForecast": {"type": "weather"},
}


def query_hyper_api(api_key, dt_from, dt_to, metrics):
    """
    Makes a request to download sensor data for specified metrics for a specified period
    of time.  Note that this gets data for _all_ sensors, and returns it as a dict,
    keyed by Aranet id.

    Arguments:
        api_key: api key for authentication
        dt_from: date range from
        dt_to: date range to
        columns: list of dictionaries containing metric names, as defined in
        READINGS_DICTS
    Return:
        success: whether data request was succesful
        error: error message
        data_df_dict: dictionary of {aranet_pro_id (str): DataFrame of sensor_data}
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + api_key,
    }
    dt_from_iso = dt_from.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    dt_to_iso = dt_to.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    url = HYPER_URL
    # get metrics as a single string, comma-separating each metric name
    metrics = ",".join(metrics)
    params = {
        "start_time": dt_from_iso,
        "end_time": dt_to_iso,
        "metrics": metrics,
        "resolution": "10m",
        "metadata": "true",
    }
    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        error = "Request's [%s] status code: %d" % (url[:70], response.status_code)
        return False, error, {}
    data = response.json()
    error = ""
    success = True
    return success, error, data


def import_hyper_data(api_key, dt_from, dt_to, create_sensors=False):
    """
    This is the main function for this module.
    Uploads data to the DTBase database, for various metrics, from the Hyper.ag API.

    Arguments:
        api_key: Hyper API key
        dt_from: date range from
        dt_to: date range to
        create_sensors: Create new sensors in the database if they don't exist. False by
            default.
    Returns:
        success, error
    """
    metrics = METRICS_TO_MEASURES.keys()
    logging.info(f"Calling Hyper API from {dt_from} to {dt_to}.")
    success, error, data = query_hyper_api(api_key, dt_from, dt_to, metrics)
    if not success:
        logging.error(error)
        return success, error
    metadata = data["metadata"]
    all_timestamps = data["labels"]
    series = data["series"]
    logging.info("Got data from Hyper for sensors.")

    if create_sensors:
        add_sensors(metadata)

    for s in series:
        metric = s["metric"]
        device_id = s["device_id"]
        device_name = metadata["devices"][device_id]["name"]
        values = s["values"]
        # Some values may be None, filter those out.
        timestamps, values = zip(
            *((t, v) for t, v in zip(all_timestamps, values) if v is not None)
        )
        logging.info(f"Uploading data for sensor {device_id}, {device_name}.")
        payload = {
            "measure_name": METRICS_TO_MEASURES[metric]["name"],
            "sensor_uniq_id": device_id,
            "readings": values,
            "timestamps": timestamps,
        }
        response = backend_call("post", "/sensor/insert_sensor_readings", payload)
        log_rest_response(response)
    logging.info("Done uploading data.")
    error = ""
    success = True
    return success, error
