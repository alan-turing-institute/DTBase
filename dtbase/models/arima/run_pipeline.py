#!/usr/bin/env python
import logging
import sys
from typing import Optional

import coloredlogs

from dtbase.core.exc import BackendCallError
from dtbase.core.utils import auth_backend_call, login
from dtbase.models.arima.arima.arima_pipeline import arima_pipeline
from dtbase.models.arima.arima.config import ConfigArima
from dtbase.models.utils.dataprocessor.clean_data import clean_data_list
from dtbase.models.utils.dataprocessor.config import (
    ConfigData,
    ConfigOthers,
    ConfigSensors,
)
from dtbase.models.utils.dataprocessor.get_data import get_training_data
from dtbase.models.utils.dataprocessor.prepare_data import prepare_data

logger = logging.getLogger(__name__)


def run_pipeline(config: Optional[dict] = None) -> None:
    # set up logging
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    field_styles = coloredlogs.DEFAULT_FIELD_STYLES
    # change the default levelname color from black to yellow
    field_styles["levelname"]["color"] = "yellow"
    coloredlogs.ColoredFormatter(field_styles=field_styles)
    coloredlogs.install(level="INFO")

    # Populate the config dictionary
    if config is None:
        config = {}
    config["data"] = ConfigData.model_validate(config.get("data", {}))
    config["sensors"] = ConfigSensors.model_validate(config.get("sensors", {}))
    config["others"] = ConfigOthers.model_validate(config.get("others", {}))
    config["arima"] = ConfigArima.model_validate(config.get("arima", {}))
    # Log into the backend
    token = login()[0]

    scenario = "Business as usual"

    # fetch training data from the database
    sensor_data = get_training_data(config=config, token=token)
    if not sensor_data:
        raise ValueError("No training data")

    # clean the training data
    cleaned_data = clean_data_list(sensor_data, config)
    prep_data = prepare_data(cleaned_data, config)

    # ensure we have the Model in the db, or insert if not
    response = auth_backend_call(
        "post", "/model/insert-model", {"name": "Arima"}, token=token
    )
    if response.status_code not in {201, 409}:
        raise BackendCallError(response)

    # ensure we have the model scenario in the db, or insert if not
    response = auth_backend_call(
        "post",
        "/model/insert-model-scenario",
        {"model_name": "Arima", "description": scenario},
        token=token,
    )
    if response.status_code not in {201, 409}:
        raise BackendCallError(response)

    # Ensure that we have all measures in the database, or insert if not.
    # We should have mean, upper bound, and lower bound for each of the measures that
    # the sensor we are trying to forecast for reports.
    base_measures_list = config["sensors"].include_measures
    logging.info(f"measures to use: {base_measures_list}")
    # base_measures_list is a list of tuples (measure_name, units)
    for base_measure_name, base_measure_units in base_measures_list:
        for m in ["Mean ", "Upper Bound ", "Lower Bound "]:
            measure = m + base_measure_name
            logging.info(f"Inserting measure {measure} to db")
            response = auth_backend_call(
                "post",
                "/model/insert-model-measure",
                {"name": measure, "units": base_measure_units, "datatype": "float"},
                token=token,
            )

    # run the ARIMA pipeline for every sensor
    sensor_unique_ids = list(prep_data.keys())
    logging.info(f"Will look at sensors {sensor_unique_ids}")
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
            mean_forecast, conf_int, metrics = arima_pipeline(values, config["arima"])
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
            response = auth_backend_call(
                "post",
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
                token=token,
            )
            if response.status_code != 201:
                raise BackendCallError(response)
            logger.info("Inserted run")


if __name__ == "__main__":
    run_pipeline()
