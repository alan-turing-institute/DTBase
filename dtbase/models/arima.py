import logging
import os
import sys
from copy import deepcopy
from datetime import timedelta
from typing import Optional, Tuple, Union

import coloredlogs
import numpy as np
import pandas as pd
import pydantic
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error
from sklearn.model_selection import TimeSeriesSplit
from statsmodels.tsa.statespace.sarimax import SARIMAX, SARIMAXResultsWrapper

from dtbase.models.utils.config import read_config
from dtbase.models.utils.dataprocessor.clean_data import clean_data, clean_data_list
from dtbase.models.utils.dataprocessor.config import (
    ConfigData,
    ConfigOthers,
    ConfigSensors,
)
from dtbase.models.utils.dataprocessor.get_data import get_training_data
from dtbase.models.utils.dataprocessor.prepare_data import prepare_data
from dtbase.services.base import BaseModel

# Read default params from config file
_config_file_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "config_arima.ini"
)
_defaults = read_config(_config_file_path, "arima")

# set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
field_styles = coloredlogs.DEFAULT_FIELD_STYLES

# change the default levelname color from black to yellow
field_styles["levelname"]["color"] = "yellow"
coloredlogs.ColoredFormatter(field_styles=field_styles)
coloredlogs.install(level="INFO")


class ConfigArima(pydantic.BaseModel):
    hours_forecast: int = pydantic.Field(
        default=_defaults["hours_forecast"], validate_default=True
    )
    arima_order: tuple[int, int, int] = pydantic.Field(
        default=_defaults["arima_order"], validate_default=True
    )
    seasonal_order: tuple[int, int, int, int] = pydantic.Field(
        default=_defaults["seasonal_order"], validate_default=True
    )
    trend: str | list[int] | None = pydantic.Field(
        default=_defaults["trend"], validate_default=True
    )
    alpha: float = pydantic.Field(default=_defaults["alpha"], validate_default=True)
    perform_cv: bool = pydantic.Field(
        default=_defaults["perform_cv"], validate_default=True
    )
    cv_refit: bool = pydantic.Field(
        default=_defaults["cv_refit"], validate_default=True
    )


class ArimaModel(BaseModel):
    def __init__(self, config: Optional[dict] = None) -> None:
        super().__init__()
        self.config = config

    @staticmethod
    def _report_errors_for_data(data: pd.Series) -> None:
        """
        Report errors if the input data is not a pandas Series indexed by timestamp.
        """
        if not isinstance(data.index, pd.DatetimeIndex):
            logger.error(
                "The time series on which to train the ARIMA model must be indexed by "
                "timestamp."
            )
            raise ValueError

    def get_config_from_config_files(self) -> ConfigArima:
        # Populate the config dictionary
        if self.config is None:
            self.config = {}
        self.config["data"] = ConfigData.model_validate(self.config.get("data", {}))
        self.config["sensors"] = ConfigSensors.model_validate(
            self.config.get("sensors", {})
        )
        self.config["others"] = ConfigOthers.model_validate(
            self.config.get("others", {})
        )
        self.config["arima"] = ConfigArima.model_validate(self.config.get("arima", {}))

    def _report_warnings_for_config(self) -> None:
        """
        Check the configuration parameters for the ARIMA model.
        Log warnings if they are not set to the default values.
        """
        arima_config = self.config["arima"]
        if arima_config.arima_order != (4, 1, 2):
            logger.warning(
                "The 'arima_order' setting in config_arima.ini"
                "has been set to something different than (4, 1, 2)."
            )
        if arima_config.seasonal_order != (1, 1, 0, 24):
            logger.warning(
                "The 'seasonal_order' setting in config_arima.ini has been set to "
                "something different than (1, 1, 0, 24)."
            )
        if arima_config.hours_forecast != 48:
            logger.warning(
                "The 'hours_forecast' setting in config_arima.ini has been set to "
                "something different than 48."
            )

    def get_training_data(self, *args: str, **kwargs: str) -> pd.Series:
        """
        Fetch training data from the database.
        """
        return get_training_data(
            config=self.config, token=self.access_token, *args, **kwargs
        )

    def clean_data(
        self, sensor_readings: pd.DataFrame, *args: str, **kwargs: str
    ) -> pd.DataFrame:
        """
        Clean the training data. Calls the function `clean_data` from the
        `dataprocessor` module. Please check that docstring for more details.
        """
        return clean_data(sensor_readings, config=self.config, *args, **kwargs)

    def clean_data_list(
        self, sensor_readings_list: pd.DataFrame, *args: str, **kwargs: str
    ) -> dict:
        """
        Clean the training data. Calls the function `clean_data_list` from the
        `dataprocessor` module. Please check that docstring for more details.
        """
        return clean_data_list(
            sensor_readings_list, config=self.config, *args, **kwargs
        )

    def prepare_data(
        self, cleaned_data: pd.DataFrame, *args: str, **kwargs: str
    ) -> dict:
        """
        Prepare the training data. Calls the function `prepare_data` from the
        `dataprocessor` module. Please check that docstring for more details.
        """
        return prepare_data(cleaned_data, config=self.config, *args, **kwargs)

    def fit(self, train_data: pd.Series) -> SARIMAXResultsWrapper:
        """
        Fit a SARIMAX statsmodels model to a
        training dataset (time series).
        The model parameters are specified through the
        `arima_order`, `seasonal_order` and `trend`
        settings in config_arima.ini.

        Parameters:
            train_data: a pandas Series containing the
                training data on which to fit the model.

        Returns:
            model_fit: the fitted model, which can now be
                used for forecasting.
        """
        arima_config = self.config["arima"]
        model = SARIMAX(
            train_data,
            order=arima_config.arima_order,
            seasonal_order=arima_config.seasonal_order,
            trend=arima_config.trend,
        )
        model_fit = model.fit(
            disp=False
        )  # fits the model by maximum likelihood via Kalman filter
        return model_fit

    def get_forecast_timestamp(self, data: pd.Series) -> pd.Timestamp:
        """
        Return the end-of-forecast timestamp.

        Parameters:
            data: pandas Series containing a time series.
                Must be indexed by timestamp.
            arima_config: A ConfigArima object containing parameters for the model.

        Returns:
            forecast_timestamp: end-of-forecast timestamp,
                calculated by adding the `hours_forecast`
                parameter of config_arima.ini to the last timestamp
                of `data`.
        """
        arima_config = self.config["arima"]
        if arima_config.hours_forecast <= 0:
            logger.error(
                "The 'hours_forecast' parameter in config_arima.ini "
                "must be greater than zero."
            )
            raise Exception
        end_of_sample_timestamp = data.index[-1]
        forecast_timestamp = end_of_sample_timestamp + timedelta(
            hours=arima_config.hours_forecast
        )
        return forecast_timestamp

    def forecast(
        self,
        model_fit: SARIMAXResultsWrapper,
        forecast_timestamp: pd.Timestamp,
    ) -> Tuple[pd.Series, pd.DataFrame]:
        """
        Produce a forecast given a trained SARIMAX model.

        Arguments:
            model_fit: the SARIMAX model fitted to training data.
                This is the output of `fit_arima`.
            forecast_timestamp: the end-of-forecast timestamp.

        Returns:
            mean_forecast: the forecast mean. A pandas Series, indexed
                by timestamp.
            conf_int: the lower and upper bounds of the confidence
                intervals of the forecasts. A pandas Dataframe, indexed
                by timestamp. Specify the confidence level through parameter
                `alpha` in config_arima.ini.
        """
        arima_config = self.config["arima"]
        alpha = arima_config.alpha
        forecast = model_fit.get_forecast(steps=forecast_timestamp).summary_frame(
            alpha=alpha
        )
        mean_forecast = forecast["mean"]  # forecast mean
        conf_int = forecast[
            ["mean_ci_lower", "mean_ci_upper"]
        ]  # get confidence intervals of forecasts
        return mean_forecast, conf_int

    def construct_cross_validator(
        self, data: pd.Series, train_fraction: float = 0.8, n_splits: int = 4
    ) -> TimeSeriesSplit:
        """
        Construct a time series cross validator (TSCV) object.

        Arguments:
            data: time series for which to construct the TSCV,
                as a pandas Series.
            train_fraction: fraction of `data` to use as the
                initial model training set. The remaining data
                will be used as the testing set in cross-validation.
            n_splits: number of splits/folds of the testing set
                for cross-validation.
        Returns:
            tscv: the TSCV object, constructed with
                sklearn.TimeSeriesSplit.
        """
        if (train_fraction < 0.5) or (train_fraction >= 1):
            logger.error(
                "The fraction of training data for cross-validation"
                "must be >= 0.5 and < 1."
            )
            raise ValueError
        n_obs = len(data)  # total number of observations
        n_obs_test = n_obs * (
            1 - train_fraction
        )  # total number of observations used for testing
        test_size = int(
            n_obs_test // n_splits
        )  # number of test observations employed in each fold
        if test_size < 1:
            logger.error(
                "A valid cross-validator cannot be built. "
                "The size of the test set is less than 1."
            )
            raise Exception
        tscv = TimeSeriesSplit(
            n_splits=n_splits, test_size=test_size
        )  # construct the time series cross-validator
        return tscv

    def cross_validate(
        self, data: pd.Series, tscv: TimeSeriesSplit, refit: bool = False
    ) -> dict:
        """
        Cross-validate a SARIMAX statsmodel model.

        Arguments:
            data: pandas Series containing the time series
                for which the SARIMAX model is built.
            tscv: the time series cross-validator object,
                returned by `construct_cross_validator`.
            refit: specify whether to refit the model
                parameters when new observations are added
                to the training set in successive cross-
                validation folds (True) or not (False).
                The default is False, as this is faster for
                large datasets.
        Returns:
            metrics: a dict containing two model metrics:
                "RMSE": the cross-validated root-mean-squared-error.
                    See `sklearn.metrics.mean_squared_error`.
                "MAPE": the cross-validated mean-absolute-percentage-error.
                    See `sklearn.metrics.mean_absolute_percentage_error`.
        """
        metrics = dict.fromkeys(["RMSE", "MAPE"])
        rmse = []  # this will hold the RMSE at each fold
        mape = []  # this will hold the MAPE score at each fold

        data_split = iter(tscv.split(data))
        # only force model fitting in the first fold
        train_index, test_index = next(data_split)
        cv_train, cv_test = data.iloc[train_index], data.iloc[test_index]
        model_fit = self.fit(cv_train)
        rmse, mape = self._update_result(model_fit, cv_test, test_index, rmse, mape)

        # loop through all folds
        for _, test_index in data_split:
            # in all other folds, the model is refitted only if requested by the user
            # here we append to the current train set the test set of the previous fold
            cv_test_old = deepcopy(cv_test)
            cv_test = data.iloc[test_index]
            if refit:
                model_fit = model_fit.append(cv_test_old, refit=True)
            else:
                # extend is faster than append with refit=False
                model_fit = model_fit.extend(cv_test_old)
            rmse, mape = self._update_result(model_fit, cv_test, test_index, rmse, mape)

        metrics["RMSE"] = np.mean(
            rmse
        )  # the cross-validated RMSE: the mean RMSE across all folds
        metrics["MAPE"] = np.mean(
            mape
        )  # the cross-validated MAPE: the mean MAPE across all folds
        return metrics

    def _update_result(
        self,
        model_fit: SARIMAXResultsWrapper,
        cv_test: pd.Series,
        test_index: pd.Series,
        rmse: list,
        mape: list,
    ) -> Tuple[list, list]:
        """
        Updates the metrics lists with the RMSE and MAPE of the current fold.
        """
        # compute the forecast for the test sample of the current fold
        forecast = model_fit.forecast(steps=len(test_index))
        # compute the RMSE for the current fold
        rmse.append(mean_squared_error(cv_test.values, forecast.values, squared=False))
        # compute the MAPE for the current fold
        mape.append(mean_absolute_percentage_error(cv_test.values, forecast.values))
        return rmse, mape

    def pipeline(
        self, data: pd.Series
    ) -> Tuple[pd.Series, pd.DataFrame, Union[dict, None]]:
        """
        Run the ARIMA model pipeline, using the SARIMAX model provided
        by the `statsmodels` library.
        The SARIMAX model parameters can be specified via the
        `config_arima.ini` file.

        Arguments:
            data: the time series on which to train the SARIMAX model,
                as a pandas Series indexed by timestamp.
        Returns:
            mean_forecast: a pandas Series, indexed by timestamp,
                containing the forecast mean. The number of hours to
                forecast into the future can be specified through the
                `config_arima.ini` file.
            conf_int: a pandas Dataframe, indexed by timestamp, containing
                the lower an upper confidence intervals for the forecasts.
            metrics: a dictionary containing the cross-validated root-mean-
                squared-error (RMSE) and mean-absolute-percentage-error (MAPE)
                for the fitted SARIMAX model. If the user requests not to perform
                cross-validation through the `config_arima.ini` file, `metrics`
                is assigned `None`.
        """

        self._report_errors_for_data(data)
        self._report_warnings_for_config()

        # perform time series cross-validation if requested by the user
        arima_config = self.config["arima"]
        cross_validation = arima_config.perform_cv
        if cross_validation:
            refit = arima_config.cv_refit
            if refit:
                logger.info(
                    "Running time series cross-validation" " WITH parameter refit..."
                )
            else:
                logger.info(
                    "Running time series cross-validation" " WITHOUT parameter refit..."
                )
            try:
                tscv = self.construct_cross_validator(data)

                try:
                    metrics = self.cross_validate(data, tscv, refit=refit)
                # TODO This except clause should be more specific.
                # What are the possible
                # errors we might expect from cross_validate_arima?
                except Exception:
                    logger.warning(
                        "Could not perform cross-validation. "
                        "Continuing without ARIMA model testing."
                    )
                    metrics = None
                else:
                    logger.info(
                        (
                            "Done running cross-validation. "
                            "The CV root-mean-squared-error is: {0:.2f}. "
                            "The CV mean-absolute-percentage-error is: {1:.3f}"
                        ).format(metrics["RMSE"], metrics["MAPE"])
                    )
            #     TODO This except clause should be more specific. What are the possible
            #     errors we might expect from construct_cross_validator?
            except Exception:
                logger.warning(
                    "Could not build a valid cross-validator. "
                    "Continuing without ARIMA model testing."
                )
                metrics = None
        else:
            metrics = None
        # fit the model and compute the forecast
        logger.info("Fitting the model...")
        model_fit = self.fit(data)
        logger.info("Done fitting the model.")
        forecast_timestamp = self.get_forecast_timestamp(data)
        logger.info("Computing forecast...")
        logger.info(
            f"Start of forecast timestamp: {data.index[-1]}."
            "End of forecast timestamp: {forecast_timestamp}"
        )

        mean_forecast, conf_int = self.forecast(model_fit, forecast_timestamp)
        logger.info("Done forecasting.")

        return mean_forecast, conf_int, metrics

    def get_service_data(self) -> None:
        """
        Runs the ARIMA model pipeline and inserts the results into the database
        via the backend.
        """

        scenario = "Business as usual"

        # fetch training data from the database
        sensor_data = self.get_training_data()
        if not sensor_data:
            raise ValueError("No training data")

        # clean the training data
        cleaned_data = self.clean_data_list(sensor_data)
        prep_data = self.prepare_data(cleaned_data)

        # ensure we have the Model in the db, or insert if not
        model_payload = [("/model/insert-model", {"name": "Arima"})]

        model_scenario = [
            (
                "/model/insert-model-scenario",
                {"model_name": "Arima", "description": scenario},
            )
        ]

        # Ensure that we have all measures in the database, or insert if not.
        # We should have mean, upper bound, and lower bound for
        # each of the measures that
        # the sensor we are trying to forecast for reports.
        base_measures_list = self.config["sensors"].include_measures
        logging.info(f"measures to use: {base_measures_list}")

        # base_measures_list is a list of tuples (measure_name, units)
        model_measures_payload = []
        for base_measure_name, base_measure_units in base_measures_list:
            for m in ["Mean ", "Upper Bound ", "Lower Bound "]:
                measure = m + base_measure_name
                model_measures_payload.append(
                    (
                        "/model/insert-model-measure",
                        {
                            "name": measure,
                            "units": base_measure_units,
                            "datatype": "float",
                        },
                    )
                )

        # run the ARIMA pipeline for every sensor
        sensor_unique_ids = list(prep_data.keys())
        logging.info(f"Will look at sensors {sensor_unique_ids}")
        model_run_payloads = []
        for sensor in sensor_unique_ids:
            base_measures_list = [
                b for b in base_measures_list if b[0] in prep_data[sensor].columns
            ]
            for base_measure in base_measures_list:
                values = prep_data[sensor][base_measure[0]]
                logger.info(
                    "running arima pipeline for %s sensor, %s measure",
                    sensor,
                    base_measure[0],
                )
                mean_forecast, conf_int, metrics = self.pipeline(values)
                mean = {
                    "measure_name": "Mean " + base_measure[0],
                    "values": list(mean_forecast),
                    "timestamps": [t.isoformat() for t in mean_forecast.index],
                }
                upper = {
                    "measure_name": "Upper Bound " + base_measure[0],
                    "values": list(conf_int.mean_ci_upper),
                    "timestamps": [t.isoformat() for t in conf_int.index],
                }
                lower = {
                    "measure_name": "Lower Bound " + base_measure[0],
                    "values": list(conf_int.mean_ci_lower),
                    "timestamps": [t.isoformat() for t in conf_int.index],
                }
                model_run_payloads.append(
                    (
                        "/model/insert-model-run",
                        {
                            "model_name": "Arima",
                            "scenario_description": scenario,
                            "measures_and_values": [mean, upper, lower],
                            "sensor_unique_id": sensor,
                            "sensor_measure": {
                                "name": base_measure[0],
                                "units": base_measure[1],
                            },
                        },
                    )
                )

        payload_pairs = (
            model_payload + model_scenario + model_measures_payload + model_run_payloads
        )
        return payload_pairs
