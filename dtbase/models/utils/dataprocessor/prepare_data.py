import datetime
import logging
from typing import Tuple

import pandas as pd
import pytz

logger = logging.getLogger(__name__)

HRS_PER_DAY = 24


def standardize_timestamp(
    timestamp: datetime.datetime, config: dict
) -> datetime.datetime:
    """
    Standardize the input timestamp according to the
    time at which the farm daily cycle starts.
    Specify the start time of the cycle using the
    `farm_cycle_start` parameter in config_arima.ini.

    Parameters:
        timestamp: a datetime object or equivalent
            (e.g. pandas Timestamp).
        config: a dictionary containing configuration parameters

    Returns:
        timestamp: the input timestamp standardised according
            the time at which the cycle starts.
            - If the time of the input timestamp is >=
            `farm_cycle_start`, the output timestamp is the date
            of the input timestamp at time `farm_cycle_start`.
            - If the time of the input timestamp is <=
            (`farm_cycle_start` - 12 hours), the output timestamp
            is the date of the input timestamp minus one day at
            time `farm_cycle_start`.
            - Otherwise, the output timestamp is the date of the
            input timestamp at time (`farm_cycle_start` - 12 hours).
    """
    farm_cycle_start = config["others"][
        "farm_cycle_start"
    ]  # time at which the farm cycle starts
    # parse string into a datetime object
    farm_cycle_start = datetime.datetime.strptime(farm_cycle_start, "%Hh%Mm%Ss")
    if farm_cycle_start.time() != datetime.time(hour=16, minute=0, second=0):
        logger.warning(
            "The `farm_cycle_start` parameter in data_config.ini has been set to "
            "something different than 4 PM."
        )
    farm_cycle_start = datetime.datetime.combine(
        timestamp.date(), farm_cycle_start.time()
    )
    farm_cycle_start = pytz.utc.localize(farm_cycle_start)
    if timestamp >= farm_cycle_start:
        timestamp = farm_cycle_start
    elif timestamp <= (farm_cycle_start - datetime.timedelta(hours=HRS_PER_DAY / 2)):
        timestamp = datetime.datetime.combine(
            (timestamp - datetime.timedelta(days=1)).date(),
            farm_cycle_start.time(),
        )
    else:
        timestamp = farm_cycle_start - datetime.timedelta(hours=HRS_PER_DAY / 2)
    return timestamp


def break_up_timestamp(data: pd.DataFrame, days_interval: int) -> pd.DataFrame:
    """
    Given an input pandas DataFrame indexed by timestamp
    and a time interval in days, break up the timestamps into
    time of the day, day of the week and a pseudo-season.

    Parameters:
        data: pandas DataFrame indexed by timestamp.
        days_interval: number of days of the time interval that
            defines the pseudo-season.

    Returns:
        data: the input pandas DataFrame with additional columns:
            - `time`: the time of the day, as a `datetime.time` object.
            - `weekday`: the day of the week with Monday=0, Sunday=6.
            - `pseudo_season`: identifies timestamps belonging to the
                same pseudo season based on the interval specified through
                `days_interval`.
    """
    # create the time-of-the-day and day-of-the-week columns
    timestamps = data.index
    data["time"] = timestamps.time
    data["weekday"] = timestamps.weekday
    # now create the pseudo-season, based on the specified interval
    delta_time = timestamps - timestamps[0]
    delta_time = delta_time.to_pytimedelta()
    interval = datetime.timedelta(days=days_interval)
    data["pseudo_season"] = delta_time // interval  # floor division
    return data


def missing_values_stats(data: pd.Series) -> float:
    """
    Return percentage of missing observations in the input
    time series.
    """
    return data.isna().sum() / len(data) * 100


def impute_missing_values(data: pd.Series, config: dict) -> pd.Series:
    """
    Replace missing values in a time series with "typically observed"
    values. This function makes use of the `days_interval` and
    `weekly_seasonality` parameters in data_config.ini.
    Note that there needs to be sufficient data in the input time series
    in order to compute typically-observed values. Otherwise, missing
    observations will not be replaced.
    Three different seasonalities are assumed in the data by default:
    daily, weekly, and pseudo-season. These seasonalities are employed
    to compute the typically-observed values that will replace missing
    values. The `weekly_seasonality` parameter can be set to `False` in
    order to remove the weekly-seasonality assumption, and the time
    interval of the pseudo-season can be modified through `days_interval`.

    Parameters:
        data: a time series as a pandas Series, potentially containing
            missing values. Must be indexed by timestamp.
        config: a dictionary containing configuration parameters

    Returns:
        data: the input time series as a pandas Series, where any missing
            values have been replaced with typically-observed values.
    """
    if not (isinstance(data, pd.Series) and isinstance(data.index, pd.DatetimeIndex)):
        logger.error(
            "The input time series must be a pandas Series indexed by timestamp."
        )
        raise ValueError
    logger.info("Replacing missing observations in " + data.name + " time series.")
    stats = missing_values_stats(data)
    logger.info("Percentage of missing observations: {0: .2f} %".format(stats))
    index_name = data.index.name  # get the index name - should be `timestamp`
    data = data.to_frame()  # first convert Series to DataFrame
    days_interval = config["others"]["days_interval"]
    data = break_up_timestamp(data, days_interval)
    # compute the mean value for the groups, excluding missing values.
    weekly_seasonality = config["others"]["weekly_seasonality"]
    # if the user has requested to consider weekly seasonality:
    if weekly_seasonality:
        if days_interval < 30:
            logger.error(
                """
                If the 'weekly_seasonality' parameter in data_config.ini is set to
                `True`, the 'days_interval' parameter must be >= 30.
                """
            )
            raise ValueError
        # the resulting DataFrame will be multi-indexed by `pseudo-season`,
        # `weekday` and `time`.
        mean_values = data.groupby(["pseudo_season", "weekday", "time"]).mean()
        # elevate the index (the timestamps) of the input data to a column
        data = data.reset_index()
        # set the index to `pseudo_season`, `weekday` and `time`
        data.set_index(["pseudo_season", "weekday", "time"], inplace=True)
    # otherwise, only consider daily and pseudo-season seasonality
    else:
        data.drop(columns="weekday", inplace=True)
        # the resulting DataFrame will be multi-indexed by `pseudo-season`
        # and `time`
        mean_values = data.groupby(["pseudo_season", "time"]).mean()
        # elevate the index (the timestamps) of the input data to a column
        data = data.reset_index()
        # set the index to `pseudo_season` and `time`
        data.set_index(["pseudo_season", "time"], inplace=True)
    # replace missing values with the computed mean values.
    # `DataFrame.update` modifies in-place, and aligns on indices.
    data.update(mean_values, overwrite=False)
    # now reset the index to be the timestamp column and make
    # sure that the rows are sorted in ascending order of index
    data.set_index(index_name, inplace=True)
    data.sort_index(ascending=True, inplace=True)
    data = data.squeeze()  # convert DataFrame back to Series
    if data.isna().any():
        logger.warning("Could not replace all missing observations.")
        stats = missing_values_stats(data)
        logger.info(
            "Percentage of remaining missing observations: {0: .2f} %".format(stats)
        )
    else:
        logger.info("Successfully removed all missing observations.")
    return data


def prepare_data(sensor_data: dict, config: dict) -> Tuple[dict, pd.DataFrame]:
    """
    Parent function of this module. Prepares the data in order to feed it into
    the model (e.g. ARIMA, HODMD, ...) pipeline. Parameters relevant to this function in
    data_config.ini are `farm_cycle_start`, `days_interval` and `weekly_seasonality`.
    The last two are employed to replace missing observations.

    Parameters:
        sensor_data: this is the output of `clean_data.clean_data`.
            A dictionary containing e.g. temperature and humidity data for
            each of the sensors, in the form of a pandas DataFrame.
        config: a dictionary containing configuration parameters

    Returns:
        sensor_data: a dictionary with the same keys as the input `sensor_data`.
            Each key is named after the corresponding sensor. The DataFrames
            contained in this dictionary are indexed by timestamp and are
            processed so that the timestamps are in agreement with the
            start of the farm cycle, specified through the parameter
            `farm_cycle_start` in data_config.ini. Missing observations will be
            replaced by "typically observed" values if there is enough data
            and the combination of parameters `days_interval` and `weekly_seasonality`
            allows it.
    """
    logger.info("Preparing the data to feed to the model...")
    if config["others"]["days_interval"] != 30:
        logger.warning(
            "The `days_interval` parameter in data_config.ini has been set to "
            "something different than 30."
        )
    if not config["others"]["weekly_seasonality"]:
        logger.warning(
            "The `weekly_seasonality` parameter in data_config.ini has been set "
            "to False."
        )
    # obtain the standardized timestamp.
    keys_sensor_data = list(sensor_data.keys())
    timestamp_standardized = standardize_timestamp(
        sensor_data[keys_sensor_data[0]].index[-1], config
    )
    # keep only the observations whose timestamp is smaller or equal to the
    # standardized timestamp

    for key in keys_sensor_data:
        sensor_data[key].drop(
            sensor_data[key][sensor_data[key].index > timestamp_standardized].index,
            inplace=True,
        )

    # if there are any missing values in the measure's time series of `sensor_data`,
    # replace them with typically observed values. Note that if there is not enough data
    # to compute typically observed values, missing observations will not be replaced.
    measures = config["sensors"]["include_measures"]
    # measures will be a list of tuples (measure_name, units)
    for key in keys_sensor_data:
        sensor_data_cols = set(sensor_data[key].columns.tolist())
        filtered_measures = sensor_data_cols.intersection(set(measures))

        for measure in filtered_measures:
            values = sensor_data[key][measure[0]]
            if values.isna().any():
                sensor_data[key][measure] = impute_missing_values(values, config)
    logger.info("Done preparing the data. Ready to feed to the model.")

    return sensor_data
