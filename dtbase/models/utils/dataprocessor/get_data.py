"""
Data access module for ARIMA model and potentially others
"""

import datetime as dt
import logging
from typing import List, Optional, Tuple

import pandas as pd

from dtbase.core.exc import BackendCallError
from dtbase.core.utils import auth_backend_call, login
from dtbase.models.utils.config import config

logger = logging.getLogger(__name__)


def remove_time_zone(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Remove timezone information from datetime columns.
    Note that all timestamps in the SQL database should be UTC.

    Parameters:
        dataframe: pandas DataFrame
    """
    new_dataframe = dataframe.select_dtypes("datetimetz")
    if not new_dataframe.empty:
        colnames = new_dataframe.columns.to_list()
        for column in colnames:
            dataframe[column] = pd.to_datetime(dataframe[column]).dt.tz_localize(None)
    return dataframe


def get_training_data(
    measures_list: Optional[List[str]] = None,
    sensors_list: Optional[List[str]] = None,
    delta_days: Optional[int] = None,
    token: Optional[str] = None,
) -> Tuple[pd.DataFrame, ...]:
    """Fetch data from one or more measures/sensors for training of the ARIMA model.

    Each output DataFrame can also be the result of joining two tables, as specified in
    the data_config.ini file.

    Args:
        measures_list (list of str): if given, override the 'include_measures' from the
            config.
        sensors_list (list of str): if given, override the 'include_sensors' from the
            config.
        delta_days (int): Number of days in the past from which to retrieve data.
            Defaults to None.
        token (str): An authencation token for the backend. Optional.

    Returns:
        tuple: A tuple of pandas DataFrames, with each corresponding to a
               Measure x Sensor combination.
               Each DataFrame is sorted by the timestamp column.
    """
    if token is None:
        token = login()[0]

    # get number of training days
    if delta_days is None:
        num_days_training = config(section="data")["num_days_training"]
    else:
        num_days_training = delta_days
    if num_days_training > 365:
        logger.error(
            "The 'num_days_training' setting in config_arima.ini cannot be set to a "
            "value greater than 365."
        )
        raise ValueError

    dt_to = dt.datetime.now()
    delta = dt.timedelta(days=num_days_training)
    dt_from = dt_to - delta
    print(f"Training data from {dt_from} to {dt_to}")
    # get one table per measure_name x sensor_uniq_id
    # each table can be produced by joining two tables, as specified in the config file.
    data_tables = []
    sensors_config = config(section="sensors")
    if not sensors_list:
        sensors_list = sensors_config["include_sensors"]
    if not measures_list:
        measures_list = sensors_config["include_measures"]
    for measure_name, units in measures_list:
        for sensor in sensors_list:
            response = auth_backend_call(
                "get",
                "/sensor/sensor-readings",
                {
                    "measure_name": measure_name,
                    "unique_identifier": sensor,
                    "dt_from": dt_from.isoformat(),
                    "dt_to": dt_to.isoformat(),
                },
                token=token,
            )
            if response.status_code != 200:
                raise BackendCallError(response)
            readings = response.json()
            entries = [
                {
                    measure_name: r["value"],
                    "sensor_unique_id": sensor,
                    "timestamp": dt.datetime.fromisoformat(r["timestamp"]),
                }
                for r in readings
            ]
            df = pd.DataFrame(entries)
            data_tables.append(df)

    # useful filter when multiple sensors and measures are specified in the
    # configuration.
    data_tables = [table for table in data_tables if len(table) > 0]
    return tuple(data_tables)
