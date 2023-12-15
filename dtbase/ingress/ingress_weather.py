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
)

# Mapping of Openweathermap metrics to sensor measures in the database.
METRICS_TO_MEASURES = {
    "temperature": {
        "name": "temperature",
        "units": "degrees Celsius",
        "datatype": "float",
    },
    "relative_humidity": {
        "name": "relative humidity",
        "units": "percent",
        "datatype": "integer",
    },
    "air_pressure": {
        "name": "air pressure",
        "units": "millibar",
        "datatype": "integer",
    },
    "wind_speed": {"name": "wind speed", "units": "m/s", "datatype": "float"},
    "wind_direction": {
        "name": "wind direction",
        "units": "degrees",
        "datatype": "integer",
    },
    "rain": {"name": "rain", "units": "mms", "datatype": "float"},
    "icon": {"name": "icon", "units": "", "datatype": "string"},
}

# Sensor types that Hyper reports data for
SENSOR_TYPES = {
    "name": "Weather",
    "description": (
        "Weather sensors and sensor-like data sources, "
        "such as weather forecast sources."
    ),
    "measures": [
        METRICS_TO_MEASURES["temperature"],
        METRICS_TO_MEASURES["relative_humidity"],
        METRICS_TO_MEASURES["air_pressure"],
        METRICS_TO_MEASURES["wind_speed"],
        METRICS_TO_MEASURES["wind_direction"],
        METRICS_TO_MEASURES["rain"],
        METRICS_TO_MEASURES["icon"],
    ],
}

# Mapping of sensor IDs to their types
SENSOR_OPENWEATHERMAPHISTORICAL = {
    "unique_identifier": "OpenWeatherMapHistory",
    "type_name": "Weather",
    "name": "OpenWeatherMap Historical Data",
}

SENSOR_OPENWEATHERMAPFORECAST = {
    "unique_identifier": "OpenWeatherMapForecast",
    "type_name": "Weather",
    "name": "OpenWeatherMap Forecasts",
}


class OpenWeatherDataIngress(BaseIngress):
    def __init__(self):
        self.present = datetime.now()

    def _set_now(self, dt: [datetime, str]):
        """
        Method to set the present time. If dt is a datetime object, then it is returned.
        If dt is the string 'present', then the present time is returned. Otherwise, an error is raised.
        The reason this is required is for the following scenario:

        If datetime.now() is used to set dt_from from outside the Class, then problems start occuring when
        comparing these times to the present time. THis is because time has continued to happen whilst initiating the class.

        For example:

        1. The user sets dt_from = datetime.now() outside the class.
        2. To determine whether to call the historical or forecast API, the class compares dt_from to the present time using datetime.now().
        3. However, time has occured between the two datetime.now() calls, meaning they are not the same although the user
        clearly means them to be.

        To avoid this, the user can set dt_from = 'present' and the class will use the present time. All times the class
        requires the present time, it can use the class constant self.present. This is set when the class is initiated.
        """
        if isinstance(dt, datetime):
            return dt
        elif dt == "present":
            return self.present
        else:
            raise ValueError(
                f"now must be either a datetime object or the string 'present'."
            )

    def _determine_if_historic_or_forecast(self, from_dt: datetime, to_dt: datetime):
        """
        Determine whether to call the historical or forecast API. This is determined by comparing the present time
        to the from_dt and to_dt. This method combined with _handling_datetime_range() should ensure the correct
        API is called or the correct error is raised.
        """
        if self.present >= to_dt:
            return CONST_OPENWEATHERMAP_HISTORICAL_URL, SENSOR_OPENWEATHERMAPHISTORICAL
        elif self.present <= from_dt:
            return CONST_OPENWEATHERMAP_FORECAST_URL, SENSOR_OPENWEATHERMAPFORECAST
        else:
            raise ValueError(
                f"Something went wrong. To help debug, the present time is {self.present}, from_dt: {from_dt} and to_dt: {to_dt}"
            )

    def _handling_datetime_range(self, from_dt: datetime, to_dt: datetime):
        """
        Performs simple checks on the datetime range to ensure it is valid. This method combined with
        _determine_if_historic_or_forecast() should ensure the correct API is called or the correct error is raised.
        """
        if from_dt > to_dt:
            raise ValueError("from_date must be before to_date")
        elif (
            from_dt < (datetime.now() - timedelta(minutes=1)) and to_dt > datetime.now()
        ):
            raise ValueError(
                "This call spans both historical and forecast data. Please make two separate calls."
            )
        else:
            pass

    def get_data(self, from_dt: [datetime, str], to_dt: [datetime, str]):
        """
        Please read the docstring for BaseIngress.get_data() for more information on this method.

        This specific implementation of get_data() calls the Openweathermap API and returns the data in the format
        required by the backend API.

        --------------------------------
        Arguments:
            from_dt: datetime, The start date range. Inclusive. If 'present' is passed, then the present time is used.
            to_dt: datetime, The end date range. Inclusive. If 'present' is passed, then the present time is used.
        Returns:
            List of tuples. A tuple should be in the format [(<endpoint_name>, <payload>)].
            It gives Sensor type, Sensor and Sensor readings.
        """
        from_dt = self._set_now(from_dt)
        to_dt = self._set_now(to_dt)
        self._handling_datetime_range(from_dt, to_dt)
        base_url, sensor_payload = self._determine_if_historic_or_forecast(
            from_dt, to_dt
        )

        logging.info(
            f"Calling Openweathermap historical API from {from_dt} to {to_dt}."
        )

        # build list of timestamps to query
        timestamps = [
            int(dt.timestamp())
            for dt in list(pd.date_range(from_dt, to_dt, freq="d").to_pydatetime())
        ]

        # Loop through timestamps, make API call and extract hourly data from response
        hourly_records = []
        error = ""
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

            # Reformat hourly data from API response into list of dicts
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

        # Limit weather_df to data between dt_from and dt_to. This is necessary because
        # the API call returns data for the whole day, not just the requested time period.
        # We could just leave all the data but I think its clearer to limit it to the
        # requested time period.
        weather_df = weather_df.loc[from_dt:to_dt]
        weather_df.to_csv(f"weather_{from_dt}_{to_dt}.csv")

        # Convert dataframe into list of dicts to match expected output format.
        # This format is required by the backend API and can be found in the readme
        # in the backend directory.

        all_timestamps = [ts.isoformat() for ts in weather_df.index]
        measure_payloads = []
        for metric in weather_df.columns:
            values = weather_df[metric]
            # Some values may be None, filter those out.
            timestamps, values = zip(
                *((t, v) for t, v in zip(all_timestamps, values) if v is not None)
            )

            measure_payloads.append(
                {
                    "measure_name": METRICS_TO_MEASURES[metric]["name"],
                    "unique_identifier": sensor_payload["unique_identifier"],
                    "readings": values,
                    "timestamps": timestamps,
                }
            )

        # Define outputs in the format (endpoint, payload)
        sensor_type_output = [("/sensor/insert-sensor-type", SENSOR_TYPES)]
        sensor_output = [("/sensor/insert-sensor", sensor_payload)]
        sensor_readings_output = [
            ("/sensor/insert-sensor-readings", payload) for payload in measure_payloads
        ]

        return sensor_type_output + sensor_output + sensor_readings_output


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
    # # Example 1: Get historical weather data for the last 2 hours
    print("----------- Test 1 ---------------")
    dt_from = datetime.now() - timedelta(hours=36)
    dt_to = "present"
    ingress = OpenWeatherDataIngress()
    output = ingress.get_data(dt_from, dt_to)
    print(output)
    print("\n")

    # Example 2: Get forecast weather data for the next 2 hours.

    print("----------- Test 2 ---------------")
    dt_from = "present"
    dt_to = datetime.now() + timedelta(hours=11)
    ingress = OpenWeatherDataIngress()
    output = ingress.get_data(dt_from, dt_to)

    print(output)
    print("\n")

    # Example 3: Try to get weather data for the last 2 hours and the next 2 hours
    print("----------- Test 3 ---------------")
    dt_from = datetime.now() - timedelta(hours=2)
    dt_to = datetime.now() + timedelta(hours=2)
    ingress = OpenWeatherDataIngress()
    try:
        output = ingress.get_data(dt_from, dt_to)
    except ValueError as e:
        print(e)
    print("\n")

    # Example 4: Try to get weather data where dt_from is after dt_to
    print("----------- Test 4 ---------------")
    dt_from = datetime.now() + timedelta(hours=2)
    dt_to = "present"
    ingress = OpenWeatherDataIngress()
    try:
        output = ingress.get_data(dt_from, dt_to)
    except ValueError as e:
        print(e)
