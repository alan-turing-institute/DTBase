"""
Data access module for ARIMA model and potentially others
"""

import datetime as dt
import logging
from typing import Optional, Tuple

import pandas as pd

from dtbase.core.exc import BackendCallError
from dtbase.core.utils import auth_backend_call, login

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
    config: dict, token: Optional[str] = None
) -> Tuple[pd.DataFrame, ...]:
    """Fetch data from one or more measures/sensors for training of the ARIMA model.

    Each output DataFrame can also be the result of joining two tables, as specified in
    the data_config.ini file.

    Args:
        config (dict): A dictionary containing the configuration parameters.
        token (str): An authencation token for the backend. Optional.

    Returns:
        tuple: A tuple of pandas DataFrames, with each corresponding to a
               Measure x Sensor combination.
               Each DataFrame is sorted by the timestamp column.
    """
    if token is None:
        token = login()[0]

    # get number of training days
    num_days_training = config["data"].num_days_training
    if num_days_training > 365:
        logger.error(
            "The 'num_days_training' setting in config_arima.ini cannot be set to a "
            "value greater than 365."
        )
        raise ValueError

    dt_to = config["data"].predict_from_datetime
    delta = dt.timedelta(days=num_days_training)
    dt_from = dt_to - delta
    logger.info(f"Training data from {dt_from} to {dt_to}")
    # get one table per measure_name x sensor_uniq_id
    # each table can be produced by joining two tables, as specified in the config file.
    data_tables = []
    sensors_config = config["sensors"]
    sensors_list = sensors_config.include_sensors
    measures_list = sensors_config.include_measures
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
