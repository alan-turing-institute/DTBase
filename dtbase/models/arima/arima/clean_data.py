from .config import config
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

constants = config(section="constants")
processing_params = config(section="data")
sensors_config = config(section="sensors")
sensors_list = sensors_config["include_sensors"]
measures_list = sensors_config["include_measures"]

def get_time_vector(start, end, frequency="1H", offset=1):
    """
    Create a vector of increasing timestamps.

    Parameters:
        start: starting timestamp.
        end: end timestamp.
        frequency: timedelta between successive timestamps,
            specified as a string. The default is "1H" (one hour).
            Must comply with pandas frequency aliases.
        offset: date offset added to the starting timestamp,
            in hours. The default is 1, as this is what was
            done in the original ARIMA R code.
    Returns:
        time_vector: a pandas dataframe, with a single column
            named "timestamp", containing the vector of increasing
            timestamps.
    """
    if offset != 1:
        logger.warning(
            "!!! The date offset added to the starting timestamp has been set to something different than 1 (hour) !!!"
        )
    # create a Pandas fixed frequency DatetimeIndex
    time_vector = pd.date_range(
        start + pd.DateOffset(hours=offset),
        end,
        freq=frequency,
    )
    time_vector = time_vector.to_frame(index=False)
    # rename the column to "timestamp"
    time_vector.rename(
        columns={list(time_vector)[0]: "timestamp"},
        inplace=True,
    )
    return time_vector


def hourly_average_sensor(sensor_data, col_names, time_vector):
    """
    Split the pandas dataframe containing the sensor data
    into the user-requested list of sensors, group by the column
    "timestamp_hour_plus_minus", and perform averaging of the
    requested columns.

    Parameters:
        sensor_data: pre-processed pandas dataframe containing the
            sensor data.
        col_names: list containing the names of the columns on
            which to perform the averaging after grouping by the
            column "timestamp_hour_plus_minus".
        time_vector: pandas dataframe containing a vector of increasing
            timestamps. Only timestamps contained in "time_vector"
            will be returned in the output ("hour_averages").
    Returns:
        hour_averages: a dict with keys named after the user-requested
            sensors, containing the columns on which averaging has been
            performed. Note that the column "timestamp_hour_plus_minus"
            is renamed to "timestamp".
    """
    hour_averages = dict.fromkeys(
        sensors_list
    )  # creates empty dict with specified keys (requested sensors)
    keys = list(hour_averages.keys())
    grouped = sensor_data.groupby("sensor_unique_id")  # group by sensor id
    for ii in range(len(hour_averages)):
        sensor = grouped.get_group(keys[ii])
        # group by column "timestamp_hour_plus_minus" and perform
        # averaging on the requested columns
        hour_averages[keys[ii]] = sensor.groupby(
            "timestamp_hour_plus_minus", as_index=False
        )[col_names].mean()
        # rename the column to "timestamp"
        hour_averages[keys[ii]].rename(
            columns={"timestamp_hour_plus_minus": "timestamp"},
            inplace=True,
        )
        # perform a left merge with "time_vector" so that only
        # timestamps contained in "time_vector" are retained
        hour_averages[keys[ii]] = pd.merge(
            time_vector,
            hour_averages[keys[ii]],
            how="left",
        )
    return hour_averages


def centered_ma(series: pd.Series, window: int = 3):
    """
    Compute a weighted centered moving average of a time series.

    Parameters:
        series: time series as a pandas series.
        window: size of the moving window (fixed number of
            observations used for each window). Must be an
            odd integer, so that the average is centered.
            The default value is 3.
    Returns:
        MA: the weighted centered moving averages, returned as a
            pandas series. NaNs are returned at both ends of the
            series, where the centered average cannot be computed
            depending on the specified window size.
    """
    if not (window % 2):
        logger.error("The moving average window must be an odd integer.")
        raise Exception
    # calculate the weights for the weighted average
    n = window - 1
    weights = np.zeros(
        window,
    )
    weights[1:-1] = 1 / n
    weights[0] = 1 / (n * 2)
    weights[-1] = 1 / (n * 2)
    # calculate the weighted centered MA, returned as a
    # pandas series
    MA = series.rolling(window=window, center=True).apply(lambda x: np.sum(weights * x))
    MA.name = MA.name + "_MA"  # rename the series
    return MA


def clean_sensor_data(sensor_data: pd.DataFrame, measures: list[str]):
    """
    Clean the pandas dataframe containing e.g. temperature and humidity data
    retrieved from the database (DB).

    Parameters:
        sensor_data: pandas dataframe containing e.g. temperature and humidity data
            returned by data_access.get_training_data.
        measures: list of strings, the names of the "measures" in the data.
    Returns:
        cleaned_data: a dictionary with keys named after the user-requested sensors.
            The corresponding values are pandas dataframes containing processed
            data for each sensor (the data is averaged based on its timestamp).
        time_vector: a pandas dataframe with a single column named "timestamp",
            containing a vector of increasing timestamps, ranging between the
            oldest and most recent timestamps in the input dataframe, with a
            timedelta between successive timestamps specified by the "time_delta"
            parameter in "config.ini".
    """
    logger.info("Cleaning sensor data...")
    # insert a new column at the end of the dataframe, named "timestamp_hour_floor",
    # that rounds the timestamp by flooring to hour precision
    sensor_data.insert(
        len(sensor_data.columns),
        "timestamp_hour_floor",
        sensor_data.timestamp.dt.floor("h"),
    )
    # create a new column, named "timedelta_in_secs", that expresses
    # the time difference, in seconds, between a timestamp and
    # itself rounded to the hour
    sensor_data["timedelta_in_secs"] = sensor_data["timestamp"].apply(
        lambda x: abs((x - x.round(freq="H")).total_seconds())
    )
    # create a new column, named "timestamp_hour_plus_minus", where any
    # timestamp "mins_from_the_hour" (minutes) before or after the hour is given
    # the timestamp of the rounded hour. Times outside this range are assigned None.
    sensor_data["timestamp_hour_plus_minus"] = sensor_data.apply(
        lambda x: x["timestamp"].round(freq="H")
        if x["timedelta_in_secs"]
        <= processing_params["mins_from_the_hour"] * constants["secs_per_min"]
        else None,
        axis=1,
    )
    # remove row entries that have been assigned None above
    sensor_data = sensor_data.dropna(subset="timestamp_hour_plus_minus")
    # create the time vector for which hourly-averaged data will be returned
    # first, parse the `time_delta` parameter of `config.ini` into total seconds.
    frequency = datetime.strptime(processing_params["time_delta"], "%Hh%Mm%Ss")
    frequency = timedelta(
        hours=frequency.hour, minutes=frequency.minute, seconds=frequency.second
    )
    frequency = int(frequency.total_seconds())
    if frequency != constants["secs_per_min"] * constants["mins_per_hr"]:
        logger.warning(
            "The 'time_delta' setting in config.ini has been set to something different than one hour."
        )
    # now create the time vector
    time_vector = get_time_vector(
        start=min(sensor_data["timestamp_hour_floor"]),
        end=max(sensor_data["timestamp_hour_floor"]),
        frequency=str(frequency) + "S",  # S for seconds
    )
    # calculate the hourly-averaged data
    cleaned_data = hourly_average_sensor(
        sensor_data,
        measures,
        time_vector,
    )
    logger.info("Done cleaning sensor data.")
    return cleaned_data, time_vector




def clean_data(sensor_readings):
    """
    Parent function of this module: clean sensor readings retrieved from the database.

    Parameters:
        sensor_readings: pandas dataframe containing e.g. temperature or humidity data
            returned by get_data.get_training_data.

    Returns:
        cleaned_data: a dictionary with keys named after the user-requested sensors.
            Use the "include_sensors" parameter in "config.ini" to specify the
            sensors. The corresponding values for the dict keys are pandas dataframes
            containing processed temperature and humidity data for each sensor
            (the observations are averaged based on the proximity of the timestamp
            to the full hour - use the "mins_from_the_hour" parameter in "config.ini"
            to specify what timestamps to average together). The processed data is
            time-ordered. The dataframes are indexed by timestamp. Specify the
            timedelta between successive timestamps using the "time_delta" parameter
            in "config.ini".
    """
    if processing_params["mins_from_the_hour"] != 15:
        logger.warning(
            "The 'mins_from_the_hour' setting in config.ini has been set to something different than 15."
        )
    if processing_params["window"] != 3:
        logger.warning(
            "The 'window' setting in config.ini has been set to something different than 3."
        )
    column_names = list(sensor_readings.columns)
    column_names.remove("sensor_unique_id")
    column_names.remove("timestamp")
    measures = column_names

    cleaned_data, time_vector = clean_sensor_data(sensor_readings, measures)

    # set the timestamp column of each of the dataframes to index
    keys = list(cleaned_data.keys())
    for key in keys:
        cleaned_data[key].set_index("timestamp", inplace=True)

    return cleaned_data
