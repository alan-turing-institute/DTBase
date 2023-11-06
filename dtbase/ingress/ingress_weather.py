"""
Python module to import data using the Openweathermap API
"""
import logging
from datetime import datetime, timedelta

import pandas as pd
import requests

from dtbase.core.constants import (
    CONST_OPENWEATHERMAP_FORECAST_URL,
    CONST_OPENWEATHERMAP_HISTORICAL_URL,
)
from dtbase.ingress.ingress_utils import (
    add_sensor_types,
    add_sensors,
    backend_call,
    log_rest_response,
)

from typing import Tuple

# Mapping of Openweathermap metrics to sensor measures in the database.
METRICS_TO_MEASURES = {
    "temperature": {
        "name": "temperature",
        "units": "degrees Celsius",
    },
    "relative_humidity": {
        "name": "relative humidity",
        "units": "percent",
    },
    "air_pressure": {
        "name": "air pressure",
        "units": "millibar",
    },
    "wind_speed": {
        "name": "wind speed",
        "units": "m/s",
    },
    "wind_direction": {
        "name": "wind direction",
        "units": "degrees",
    },
    "rain": {
        "name": "rain",
        "units": "mms",
    },
    "icon": {
        "name": "icon",
        "units": "",
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
                "datatype": "integer",
            },
            {
                "name": "air pressure",
                "units": "millibar",
                "datatype": "integer",
            },
            {
                "name": "wind speed",
                "units": "m/s",
                "datatype": "float",
            },
            {
                "name": "wind direction",
                "units": "degrees",
                "datatype": "integer",
            },
            {
                "name": "rain",
                "units": "mm",
                "datatype": "float",
            },
            {
                "name": "icon",
                "units": "",
                "datatype": "string",
            },
        ],
    },
]


# Mapping of sensor IDs to their types
SENSORS = [
    {"unique_identifier": "OpenWeatherMapHistory", "type_name": "weather"},
    {"unique_identifier": "OpenWeatherMapForecast", "type_name": "weather"},
]


def query_openweathermap_api(dt_to: datetime) -> Tuple[bool, str, pd.DataFrame]:
    """
    Retrieve weather data from the openweathermap API.
    If dt_to is in the past, return historical data, or if it is in the
    future, return forecast data.
    Note that for historical data, each API call returns the hourly data
    from 00:00 to 23:59 on the date specified by the 'dt' timestamp,
    so we need to make 2 calls in order to get the full set of data for
    the last 24 hours.

    Parameters
    ----------
    dt_to: datetime, latest time for returned records

    Returns
    -------
    success: bool, True if everything OK
    error: str, empty string if everything OK
    df: pd.DataFrame, contains 1 row per hours data.
    """
    timestamps = []
    if dt_to <= datetime.now():
        base_url = CONST_OPENWEATHERMAP_HISTORICAL_URL
        dt_from = dt_to - timedelta(days=2)
        timestamps.append(int(dt_from.timestamp()))
        logging.info(
            f"Calling Openweathermap historical API from {dt_from} to {dt_to}."
        )
    else:
        base_url = CONST_OPENWEATHERMAP_FORECAST_URL
        logging.info(f"Calling Openweathermap forecast API to {dt_to}.")

    timestamps.append(int(dt_to.timestamp()))
    hourly_records = []
    error = ""
    # do API call and get data in right format for both dates.
    for ts in timestamps:
        url = base_url + "&dt={}".format(ts)
        response = requests.get(url)

        if response.status_code != 200:
            error = "Request's [%s] status code: %d" % (
                url[: min(70, len(url))],
                response.status_code,
            )
            success = False
            return success, error, None
        hourly_data = response.json()["hourly"]

        for hour in hourly_data:
            record = {}
            record["timestamp"] = datetime.fromtimestamp(hour["dt"])
            record["temperature"] = hour["temp"]
            record["air_pressure"] = hour["pressure"]
            record["relative_humidity"] = hour["humidity"]
            record["wind_speed"] = hour["wind_speed"]
            record["wind_direction"] = hour["wind_deg"]
            record["icon"] = hour["weather"][0]["icon"]
            record["rain"] = 0.0
            if "rain" in hour.keys():
                record["rain"] += hour["rain"]["1h"]
            hourly_records.append(record)
    weather_df = pd.DataFrame(hourly_records)
    weather_df.set_index("timestamp", inplace=True)
    success = True
    log = "\nSuccess: Weather dataframe \n{}".format(weather_df)
    logging.info(log)
    return success, error, weather_df


def import_openweathermap_data(dt_to: datetime, sensor_uniq_id: str, 
                            create_sensors: bool=False) -> Tuple[bool, str]:
    """
    This is the main function for this module.
    Uploads data to the DTBase database, for various metrics, from the
    Openweathermap API.  If dt_to is in the past, this will be historical
    data, while if it is in the future, it will be forecast data.

    Arguments:
        dt_to:datetime date range to
        sensor_uniq_id: str, either "OpenWeatherMapHistory" or "OpenWeatherMapForecast"
        create_sensors: Create new sensors in the database if they don't exist. False by
            default.
    Returns:
        success, error
    """
    success, error, df = query_openweathermap_api(dt_to)
    if not success:
        logging.error(error)
        return success, error

    all_timestamps = [ts.isoformat() for ts in df.index]

    if create_sensors:
        add_sensor_types(SENSOR_TYPES)
        add_sensors(SENSORS)

    for metric in df.columns:
        values = df[metric]
        # Some values may be None, filter those out.
        timestamps, values = zip(
            *((t, v) for t, v in zip(all_timestamps, values) if v is not None)
        )
        logging.info(f"Uploading data for sensor {sensor_uniq_id}.")

        payload = {
            "measure_name": METRICS_TO_MEASURES[metric]["name"],
            "unique_identifier": sensor_uniq_id,
            "readings": values,
            "timestamps": timestamps,
        }

        response = backend_call("post", "/sensor/insert-sensor-readings", payload)
        log_rest_response(response)
    logging.info("Done uploading data.")
    error = ""
    success = True
    return success, error
