"""
Python module to import data using the Openweathermap API
"""
import logging
from datetime import datetime, timedelta
from typing import Tuple

import pandas as pd
import requests

from dtbase.core.constants import (
    CONST_OPENWEATHERMAP_FORECAST_URL,
    CONST_OPENWEATHERMAP_HISTORICAL_URL,
)
from dtbase.ingress.ingress_base import (
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

# Type of sensor for OpenWeatherMap
SENSOR_TYPE = {
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

# Two different Sensor depending on whether its forecast or historical
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
    """
    Custom class inheriting from the BaseIngress class for interacting with the
    OpenWeatherData API.
    """

    def __init__(self) -> None:
        super().__init__()
        self.present = datetime.now()

    def _set_now(self, dt: [datetime, str]) -> datetime:
        """
        Method to set the present time. If dt is a datetime object, then it is returned.
        If dt is the string 'present', then the present time is returned.
        Otherwise, an error is raised.
        The reason this is required is for the following scenario:

        If datetime.now() is used to set dt_from from outside the Class, then problems
        start occuring when comparing these times to the present time. THis is because
        time has continued to happen whilst initiating the class.

        For example:

        1. The user sets dt_from = datetime.now() outside the class.
        2. To determine whether to call the historical or forecast API,
        the class compares dt_from to the present time using datetime.now().
        3. However, time has occured between the two datetime.now() calls,
        meaning they are not the same although the user
        clearly means them to be.

        To avoid this, the user can set dt_from = 'present' and the class will
        use the present time. All times the class requires the present time,
        it can use the class constant self.present.
        This is set when the class is initiated.
        """
        if isinstance(dt, datetime):
            return dt
        elif dt == "present":
            return self.present
        else:
            raise ValueError(
                "now must be either a datetime object or the string 'present'."
            )

    def _determine_if_historic_or_forecast(
        self,
        from_dt: datetime,
        to_dt: datetime,
        override_inferred_weather_api: [None, str] = None,
    ) -> Tuple[str, str]:
        """
        Determine whether to call the historical or forecast API.
        This is determined by comparing the present time to the from_dt and to_dt.
        This method combined with _handling_datetime_range() should ensure the correct
        API is called or the correct error is raised.

        override_inferred_weather_api: str, Optional.
            options are "historical" or "forecast". This overrides
            the inferred weather API. Practically, this is used
            for testing purposes.
        """
        if override_inferred_weather_api is not None:
            if override_inferred_weather_api == "historical":
                return (
                    CONST_OPENWEATHERMAP_HISTORICAL_URL,
                    SENSOR_OPENWEATHERMAPHISTORICAL,
                )
            elif override_inferred_weather_api == "forecast":
                return CONST_OPENWEATHERMAP_FORECAST_URL, SENSOR_OPENWEATHERMAPFORECAST
            else:
                raise ValueError(
                    "override_inferred_weather_api must be either 'historical' or"
                    " 'forecast'"
                )

        if self.present >= to_dt:
            return CONST_OPENWEATHERMAP_HISTORICAL_URL, SENSOR_OPENWEATHERMAPHISTORICAL
        elif self.present <= from_dt:
            return CONST_OPENWEATHERMAP_FORECAST_URL, SENSOR_OPENWEATHERMAPFORECAST
        else:
            raise ValueError(
                "Some unforeseen combinations of from_dt and to_dt has been given.    "
                f"             To help debug, the present time is {self.present},"
                f" from_dt: {from_dt}                 and to_dt: {to_dt}"
            )

    def _handling_datetime_range(self, from_dt: datetime, to_dt: datetime) -> None:
        """
        Performs simple checks on the datetime range to ensure it is valid.
        This method combined with _determine_if_historic_or_forecast() should ensure
        the correct API is called or the correct error is raised.
        """
        if from_dt > to_dt:
            raise ValueError("from_date must be before to_date")
        elif from_dt < self.present and to_dt > self.present:
            raise ValueError(
                "This call spans both historical and forecast data.                "
                " Please make two separate calls."
            )
        elif from_dt < (self.present - timedelta(days=5)):
            raise ValueError(
                "from_dt cannot be more than 5 days in the past.                    "
                f" Current value is: {from_dt}"
            )
        elif to_dt > self.present + timedelta(days=2):
            raise ValueError(
                "to_dt cannot be more than 2 days in the future.                     "
                f" Current value is: {to_dt}"
            )
        # Check from_dt and to_dt are at least an hour apart
        elif (to_dt - from_dt) < timedelta(hours=1):
            raise ValueError(
                "from_dt and to_dt must be at least an hour apart.                    "
                f" Current values are: {from_dt} and {to_dt}"
            )
        else:
            pass

    def get_api_base_url_and_sensor(
        self,
        from_dt: [datetime, str],
        to_dt: [datetime, str],
        override_inferred_weather_api: [None, str] = None,
    ) -> Tuple[str, str, datetime, datetime]:
        from_dt = self._set_now(from_dt)
        to_dt = self._set_now(to_dt)
        self._handling_datetime_range(from_dt, to_dt)
        base_url, sensor_payload = self._determine_if_historic_or_forecast(
            from_dt, to_dt, override_inferred_weather_api=override_inferred_weather_api
        )
        return base_url, sensor_payload, from_dt, to_dt

    def get_data(
        self,
        from_dt: [datetime, str],
        to_dt: [datetime, str],
        override_inferred_weather_api: [None, str] = None,
    ) -> list:
        """
        Please read the docstring for BaseIngress.get_data()
        for more information on this method.

        This specific implementation of get_data() calls the Openweathermap API
        and returns the data in the format required by the backend API.

        There are two different OpenWeather APIs, one for historical data and one
        for forecast data. This method determines which API to call based on the
        from_dt and to_dt. If dt_from/dt_to are both in the past/present then the
        hsitorical API will be called. On the other hand, if dt_from/dt_to are both
        in the future/present then the forecast API will be called.
        If dt_from and dt_to span both the past and future, then an error is raised.

        Note the georgraphical location is defined by the
        two environment variables DT_LAT and DT_LONG.

        --------------------------------
        Arguments:
            from_dt: datetime, The start date range. Inclusive.
            Max 5 days in the past.
            If 'present' is passed, then the present time is used.
            DON'T USE datetime.now() as this will cause problems.
            to_dt: datetime, The end date range. Inclusive.
            Max 2 days in the future.
            If 'present' is passed, then the present time is used.
            DON'T USE datetime.now() as this will cause problems.
            override_inferred_weather_api: str, Optional.
            options are "historical" or "forecast". This overrides
            the inferred weather API. Practically, this is used
            for testing purposes.

        Returns:
            List of tuples. A tuple should be in the format
            [(<endpoint_name>, <payload>)].
            It gives Sensor type, Sensor and Sensor measurements.
        """
        base_url, sensor_payload, from_dt, to_dt = self.get_api_base_url_and_sensor(
            from_dt, to_dt, override_inferred_weather_api=override_inferred_weather_api
        )

        logging.info(f"Calling Openweathermap API from {from_dt} to {to_dt}.")

        # build list of timestamps to query for each day in the range
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
        # the API call returns data for the whole day, not just the requested time
        # period. We could just leave all the data but I think its clearer
        # to limit it to the requested time period.
        weather_df = weather_df[
            (weather_df.index >= from_dt) & (weather_df.index <= to_dt)
        ]

        print(weather_df)

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
        sensor_type_output = [("/sensor/insert-sensor-type", SENSOR_TYPE)]
        sensor_output = [("/sensor/insert-sensor", sensor_payload)]
        sensor_readings_output = [
            ("/sensor/insert-sensor-readings", payload) for payload in measure_payloads
        ]

        return sensor_type_output + sensor_output + sensor_readings_output


def example_weather_ingress() -> None:
    """
    Ingress weather data from 60 hours before today and 2 days after.
    As there are two different APIs used for past and future, we need to make two
    seperate calls. This is likely to be specific to the weather ingress. Other
    ingress methods may not need to do this.
    """

    # First do calls from before now
    dt_from = datetime.now() - timedelta(hours=2)
    dt_to = "present"
    weather_ingress = OpenWeatherDataIngress()
    weather_ingress.ingress_data(dt_from, dt_to)

    # Now repeat for after
    dt_from = "present"
    dt_to = datetime.now() + timedelta(hours=3)
    weather_ingress = OpenWeatherDataIngress()
    weather_ingress.ingress_data(dt_from, dt_to)


if __name__ == "__main__":
    example_weather_ingress()
