"""
Python module to import data using the Openweathermap API
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

import pandas as pd
import requests

from dtbase.core.constants import (
    CONST_OPENWEATHERMAP_FORECAST_URL,
    CONST_OPENWEATHERMAP_HISTORICAL_URL,
)
from dtbase.ingress.ingress_utils import (
    BaseIngress,
    add_sensor_types,
    add_sensors,
    backend_call,
    backend_login,
    log_rest_response,
)

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
        "name": "Weather",
        "description": (
            "Weather sensors and sensor-like data sources, "
            "such as weather forecast sources."
        ),
        "measures": [
            METRICS_TO_MEASURES["temperature"] | {"datatype": "float"},
            METRICS_TO_MEASURES["relative_humidity"] | {"datatype": "integer"},
            METRICS_TO_MEASURES["air_pressure"] | {"datatype": "integer"},
            METRICS_TO_MEASURES["wind_speed"] | {"datatype": "float"},
            METRICS_TO_MEASURES["wind_direction"] | {"datatype": "integer"},
            METRICS_TO_MEASURES["rain"] | {"datatype": "float"},
            METRICS_TO_MEASURES["icon"] | {"datatype": "string"},
        ],
    },
]


# Mapping of sensor IDs to their types
SENSORS = [
    {
        "unique_identifier": "OpenWeatherMapHistory",
        "type_name": "Weather",
        "name": "OpenWeatherMap Historical Data",
    },
    {
        "unique_identifier": "OpenWeatherMapForecast",
        "type_name": "Weather",
        "name": "OpenWeatherMap Forecasts",
    },
]


class OpenWeatherDataIngress(BaseIngress):
    def get_data():
        """
        Method for getting data from source and returning Backend API Endpoints names
        and payload pairs.
        The method should return a list of tuples. A tuple should
        be in the format [(<endpoint_name>, <payload>)]. It must be a list even if
        its a single tuple.

        Below is an example for inserting a sensor type and a sensor.
        Please look at backend readme for list of backend endpoints
        and their repsective payload formats.

        [
            (
                "/sensor/insert-sensor-type",
                {
                    "name": "Weather",
                    "description": (
                        "Weather sensors and sensor-like data sources, "
                        "such as weather forecast sources."
                    ),
                    "measures": [
                        {
                            "name": "temperature",
                            "units": "degrees Celsius",
                            "datatype": "float",
                        },
                        {"name": "relative humidity", "units": "percent", "datatype": "float"},
                    ],
                },
            ),
            (
                "/sensor/insert-sensor",
                {
                    "unique_identifier": "OpenWeatherMapHistory",
                    "type_name": "Weather",
                    "name": "OpenWeatherMap Historical Data",
                },
            ),
        ]

        """
        raise NotImplementedError()


def query_openweathermap_api(
    dt_to: datetime,
    **timedelta_kwargs: int,
) -> Tuple[bool, str, Optional[pd.DataFrame]]:
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
    days: int, number of days to retrieve data going back in time from dt_to.
      Default is 2. Parameter is ignored if dt_to is in the future.
    **timedelta_kwargs: keyword arguments to pass to timedelta,
    e.g. hours=1, minutes=30, etc.

    Returns
    -------
    success: bool, True if everything OK
    error: str, empty string if everything OK
    df: pd.DataFrame, contains 1 row per hours data.
    """
    # timestamps = []
    if dt_to <= datetime.now():
        base_url = CONST_OPENWEATHERMAP_HISTORICAL_URL
        dt_from = dt_to - timedelta(**timedelta_kwargs)
        # timestamps.append(int(dt_from.timestamp()))
        logging.info(
            f"Calling Openweathermap historical API from {dt_from} to {dt_to}."
        )
    else:
        base_url = CONST_OPENWEATHERMAP_FORECAST_URL
        dt_from = datetime.now()
        logging.info(f"Calling Openweathermap forecast API from {dt_from} to {dt_to}.")

    timestamps = [
        int(dt.timestamp())
        for dt in list(pd.date_range(dt_from, dt_to, freq="d").to_pydatetime())
    ]

    print(timestamps)

    # timestamps.append(int(dt_to.timestamp()))
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

    weather_df.to_csv(f"Testing_{dt_from}-{dt_to}.csv")
    success = True
    log = "\nSuccess: Weather dataframe \n{}".format(weather_df)
    logging.info(log)
    return success, error, weather_df


def import_openweathermap_data(
    dt_to: datetime,
    sensor_uniq_id: str,
    backend_user: str,
    backend_password: str,
    create_sensors: bool = False,
    **timedelta_kwargs: int,
) -> Tuple[bool, str]:
    """
    This is the main function for this module.
    Uploads data to the DTBase database, for various metrics, from the
    Openweathermap API.  If dt_to is in the past, this will be historical
    data, while if it is in the future, it will be forecast data.

    Arguments:
        dt_to:datetime date range to
        sensor_uniq_id: str, either "OpenWeatherMapHistory" or "OpenWeatherMapForecast"
        backend_user: str, email of the user to login to the backend
        backend_password: str, password for that user
        create_sensors: Create new sensors in the database if they don't exist. False by
            default.
    Returns:
        success, error
    """

    # Check that the sensor_uniq_id is in valid options defined in SENSORS
    if sensor_uniq_id not in [sensor["unique_identifier"] for sensor in SENSORS]:
        error = f"Invalid sensor_uniq_id: {sensor_uniq_id}"
        logging.error(error)
        return False, error

    access_token = backend_login(backend_user, backend_password)
    success, error, df = query_openweathermap_api(dt_to, **timedelta_kwargs)
    if not success:
        logging.error(error)
        return success, error
    assert df is not None

    all_timestamps = [ts.isoformat() for ts in df.index]

    if create_sensors:

        # Filter out the sensor we want to create based on sensor_uniq_id
        add_sensors(
            [
                sensor
                for sensor in SENSORS
                if sensor["unique_identifier"] == sensor_uniq_id
            ],
            access_token=access_token,
        )

        add_sensor_types(SENSOR_TYPES, access_token=access_token)

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

        response = backend_call(
            "post", "/sensor/insert-sensor-readings", payload, access_token=access_token
        )
        log_rest_response(response)
    logging.info("Done uploading data.")
    error = ""
    success = True
    return success, error


if __name__ == "__main__":

    # Set DT_LONG and DT_LAT environment variables to your location

    # Test historical query 4 days from past
    now = datetime.now()
    success, error, df = query_openweathermap_api(dt_to=now, days=3)

    # Test forecast query 4 days into future
    future = datetime.now() + timedelta(days=4)
    success, error, df = query_openweathermap_api(dt_to=future, days=3)

    # # Example Weather Forecast usage:
    # dt_to = datetime.now() + timedelta(days=2)
    # sensor_uniq_id = "OpenWeatherMapForecast"
    # import_openweathermap_data(
    #     dt_to,
    #     sensor_uniq_id,
    #     create_sensors=True,
    #     backend_user=DEFAULT_USER_EMAIL,
    #     backend_password=DEFAULT_USER_PASS,
    # )

    # dt_to = datetime.now() - timedelta(hours=48)
    # sensor_uniq_id = "OpenWeatherMapHistory"
    # import_openweathermap_data(
    #     dt_to,
    #     sensor_uniq_id,
    #     create_sensors=True,
    #     backend_user=DEFAULT_USER_EMAIL,
    #     backend_password=DEFAULT_USER_PASS,
    # )
