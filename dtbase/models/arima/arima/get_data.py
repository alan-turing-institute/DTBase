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

from dtbase.core.db import connect_db, session_open, session_close
from dtbase.core.sensors import (
    get_sensor_readings
)

from dtbase.core.constants import SQL_CONNECTION_STRING, SQL_DBNAME
from dtbase.core.utils import query_result_to_array

logger = logging.getLogger(__name__)


def get_sqlalchemy_session(connection_string=None, dbname=None):
    """
    For other functions in this module, if no session is provided as an argument,
    they will call this to get a session using default connection string.
    """
    if not connection_string:
        connection_string = SQL_CONNECTION_STRING
    if not dbname:
        dbname = SQL_DBNAME
    status, log, engine = connect_db(connection_string, dbname)
    session = session_open(engine)
    return session


def print_rows_head(rows, numrows=0):
    logging.info("Printing:{0} of {1}".format(numrows, len(rows)))
    if numrows == 0:
        for row in rows[: len(rows)]:
            logging.info(row)
    else:
        for row in rows[:numrows]:
            logging.info(row)


def get_days_weather(num_days=2, num_rows=5, session=None):
    """
    Get 5 rows of weather data [(timestamp:datetime, temp:float, humid:float),...]
    """
    if not session:
        session = get_sqlalchemy_session()
    date_to = datetime.datetime.now()
    delta = datetime.timedelta(days=num_days)
    date_from = date_to - delta
    query = (
        session.query(
            ReadingsWeatherClass.timestamp,
            ReadingsWeatherClass.temperature,
            ReadingsWeatherClass.relative_humidity,
        )
        .filter(ReadingsWeatherClass.timestamp > date_from)
        .order_by(asc(ReadingsWeatherClass.timestamp))
        .limit(num_rows)
    )
    result = session.execute(query.statement).fetchall()
    session_close(session)
    return result


def get_days_weather_forecast(num_days=2, session=None):
    if not session:
        session = get_sqlalchemy_session()
    date_from = datetime.datetime.now()
    delta = datetime.timedelta(days=num_days)
    date_to = date_from + delta
    # allow for a delay of 24 hours from current time to ensure that there are
    # no gaps between historical weather data (retrieved from table iweather)
    # and forecast weather data (retrieved from table weather_forecast)
    date_from = date_from - datetime.timedelta(hours=24)
    query = (
        session.query(
            WeatherForecastsClass.timestamp,
            WeatherForecastsClass.temperature,
            WeatherForecastsClass.relative_humidity,
            WeatherForecastsClass.time_created,
        )
        .filter(WeatherForecastsClass.timestamp > date_from)
        .filter(WeatherForecastsClass.timestamp < date_to)
        .order_by(
            WeatherForecastsClass.timestamp, desc(WeatherForecastsClass.time_created)
        )
        .distinct(WeatherForecastsClass.timestamp)
    )
    result = session.execute(query.statement).fetchall()
    session_close(session)
    # drop the time_created (the last element) from each row
    return [r[:3] for r in result]


def get_days_humidity_temperature(
    delta_days=10, num_rows=5, sensor_id=27, session=None
):
    if not session:
        session = get_sqlalchemy_session()
    date_to = datetime.datetime.now()
    delta = datetime.timedelta(days=delta_days)
    date_from = date_to - delta
    query = (
        session.query(
            ReadingsAranetTRHClass.timestamp,
            ReadingsAranetTRHClass.temperature,
            ReadingsAranetTRHClass.humidity,
        )
        .filter(ReadingsAranetTRHClass.sensor_id == sensor_id)
        .filter(ReadingsAranetTRHClass.timestamp > date_from)
        .limit(num_rows)
    )
    result = session.execute(query.statement).fetchall()
    session_close(session)
    return result


def get_days_humidity(delta_days=10, num_rows=5, sensor_id=27, session=None):
    """
    almost the same as get_days_humidity - just run that and get the first
    and third elements of the output tuples.
    """
    result = get_days_humidity_temperature(delta_days, num_rows, sensor_id, session)
    return [(r[0], r[2]) for r in result]


def get_datapoint_humidity(sensor_id=27, num_rows=1, session=None):
    if not session:
        session = get_sqlalchemy_session()
    query = (
        session.query(ReadingsAranetTRHClass.timestamp, ReadingsAranetTRHClass.humidity)
        .filter(ReadingsAranetTRHClass.sensor_id == sensor_id)
        .order_by(desc(ReadingsAranetTRHClass.timestamp))
        .limit(num_rows)
    )
    result = session.execute(query.statement).fetchall()
    session_close(session)
    return result


def get_datapoint(filepath=None, **kwargs):
    if filepath:
        LastDataPoint = pd.read_csv(filepath)
        jj = np.size(LastDataPoint, 1)
        if jj > 1:
            DataPoint = float(LastDataPoint[str(jj)])
        else:
            DataPoint = 0.5  # dummy value
        return DataPoint
    else:
        dp_database = np.asarray(get_datapoint_humidity(**kwargs))[0, 1]
        return dp_database




# arima -----------------------------------------------------------------------


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


def get_training_data(
    measures=None,
    delta_days=None,
    session=None,
    arima_config=None,
):
    """Fetch data from one or more measures/sensors for training of the ARIMA model.

    Each output DataFrame can also be the result of joining two tables, as specified in
    the config.ini file.

    Args:
        measures (dict): Dictionary where the keys are the names of SensorMeasures,
            and the values are lists of Sensor uniq_ids for the sensors from which
            we want values for those measures. e.g.:
            {"Temperature": ["TRHsensor1", "TRHsensor2"], "Humidity": ["TRHsensor1"]}
        delta_days (int): Number of days in the past from which to retrieve data.
            Defaults to None.
        num_rows (int, optional): Number of rows to limit the data to. Defaults to None.
        session (_type_, optional): _description_. Defaults to None.
        arima_config: A function that can be called to return various sections of the
            Arima config.

    Returns:
        tuple: A tuple of pandas DataFrames, with each corresponding to a
               Measure x Sensor combination.
               Each DataFrame is sorted by the timestamp column.
    """

    # get number of training days
    if delta_days is None:
        num_days_training = arima_config(section="data")["num_days_training"]
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
    for measure in measures.keys():
        for sensor in measures[measure]:
            columns = [measure, "sensor_unique_id", "timestamp"]
            readings = get_sensor_readings(
                measure_name=measure,
                sensor_uniq_id=sensor,
                dt_from=date_from,
                dt_to=date_to,
                session=session
            )
            entries = [
                {measure: r[0], "sensor_unique_id": sensor, "timestamp": r[1]} \
                for r in readings
            ]
            df = pd.DataFrame(entries)
            data_tables.append(df)

    session_close(session)
    return tuple(data_tables)
