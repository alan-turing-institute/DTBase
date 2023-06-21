"""
Data access module for ARIMA model and potentially others
"""

import logging
import sys
import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import desc, asc, exc, func

from dtbase.core.sensors import get_sensor_readings

from dtbase.models.utils.db_utils import get_sqlalchemy_session, session_close
from dtbase.models.utils.config import config

logger = logging.getLogger(__name__)


def remove_time_zone(dataframe: pd.DataFrame):
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
    measures_list=None,
    sensors_list=None,
    delta_days=None,
    session=None,
):
    """Fetch data from one or more measures/sensors for training of the ARIMA model.

    Each output DataFrame can also be the result of joining two tables, as specified in
    the data_config.ini file.

    Args:
        measures_list (list of str): if given, override the 'include_measures' from the config.
        sensors_list (list of str): if given, override the 'include_sensors' from the config.
        delta_days (int): Number of days in the past from which to retrieve data.
            Defaults to None.
        num_rows (int, optional): Number of rows to limit the data to. Defaults to None.
        session (_type_, optional): _description_. Defaults to None.

    Returns:
        tuple: A tuple of pandas DataFrames, with each corresponding to a
               Measure x Sensor combination.
               Each DataFrame is sorted by the timestamp column.
    """

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

    if not session:
        session = get_sqlalchemy_session()
    date_to = datetime.datetime.now()
    delta = datetime.timedelta(days=num_days_training)
    date_from = date_to - delta
    print(f"Training data from {date_from} to {date_to}")
    # get one table per measure_name x sensor_uniq_id
    # each table can be produced by joining two tables, as specified in the config file.
    data_tables = []
    sensors_config = config(section="sensors")
    if not sensors_list:
        sensors_list = sensors_config["include_sensors"]
    if not measures_list:
        measures_list = sensors_config["include_measures"]
        # this will be a list of tuples (measure_name, units)
    for measure in measures_list:
        for sensor in sensors_list:
            columns = [measure[0], "sensor_unique_id", "timestamp"]
            readings = get_sensor_readings(
                measure_name=measure[0],
                sensor_uniq_id=sensor,
                dt_from=date_from,
                dt_to=date_to,
                session=session,
            )
            entries = [
                {measure[0]: r[0], "sensor_unique_id": sensor, "timestamp": r[1]}
                for r in readings
            ]
            df = pd.DataFrame(entries)
            data_tables.append(df)

    # useful filter when multiple sensors and measures are specified in the configuration.
    data_tables = [table for table in data_tables if len(table) > 0]
    
    session_close(session)
    return tuple(data_tables)
