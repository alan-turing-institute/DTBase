#!/usr/bin/env python
import logging
import sys
from typing import Dict, List, Optional, Tuple

import coloredlogs
import pandas as pd

from dtbase.core.exc import BackendCallError
from dtbase.core.utils import auth_backend_call, login
from dtbase.models.hodmd.hodmd_model import hodmd_pipeline
from dtbase.models.utils.dataprocessor.clean_data import clean_data_list
from dtbase.models.utils.dataprocessor.config import (
    ConfigData,
    ConfigOthers,
    ConfigSensors,
)
from dtbase.models.utils.dataprocessor.get_data import get_training_data
from dtbase.models.utils.dataprocessor.prepare_data import prepare_data

logging.getLogger("matplotlib").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def fetch_data(config: dict) -> Tuple[Dict, pd.DataFrame]:
    # fetch training data from the database
    sensor_data = get_training_data(config)
    if not sensor_data:
        raise ValueError("No training data")

    # clean the training data
    cleaned_data = clean_data_list(sensor_data, config)

    # prepare the clean data for the HODMD model
    prep_data = prepare_data(cleaned_data, config)

    return prep_data


def run_pipeline(
    plots_save_path: Optional[str] = None,
    multi_measure: bool = False,
    config: Optional[dict] = None,
) -> None:
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

    # Log into the backend
    token = login()[0]

    prep_data = fetch_data(config)

    scenario = "Business as usual"
    # ensure we have the Model in the db, or insert if not
    response = auth_backend_call(
        "post", "/model/insert-model", {"name": "HODMD"}, token=token
    )
    if response.status_code not in {201, 409}:
        raise BackendCallError(response)

    # ensure we have the model scenario in the db, or insert if not
    response = auth_backend_call(
        "post",
        "/model/insert-model-scenario",
        {"model_name": "HODMD", "description": scenario},
        token=token,
    )
    if response.status_code not in {201, 409}:
        raise BackendCallError(response)

    # Ensure that we have all measures in the database, or insert if not.
    measures_list = config["sensors"].include_measures
    logging.info(f"measures to use: {measures_list}")
    # base_measures_list is a list of tuples (measure_name, units)
    for measure_name, measure_units in measures_list:
        logging.info(f"Inserting measure {measure_name} to db")
        response = auth_backend_call(
            "post",
            "/model/insert-model-measure",
            {"name": measure_name, "units": measure_units, "datatype": "float"},
            token=token,
        )

    # run the HODMD pipeline for every sensor
    sensor_unique_ids = config["sensors"].include_sensors

    # run HODMD pipeline
    if multi_measure:
        hodmd_multi_measure(
            prep_data,
            sensor_unique_ids,
            measures_list,
            scenario,
            plots_save_path,
            token,
        )
    else:
        hodmd_single_measure(
            prep_data,
            sensor_unique_ids,
            measures_list,
            scenario,
            plots_save_path,
            token,
        )


def hodmd_single_measure(
    prep_data: pd.DataFrame,
    sensor_unique_ids: List[(str | int)],
    measures_list: List[Tuple[str, str]],
    scenario: str,
    save_path: str,
    token: str,
) -> None:
    # loop through every sensor
    for sensor in sensor_unique_ids:
        # filter measures_list: only retrieve measures related to the current sensor
        sensor_measures = [
            m for m in measures_list if m[0] in prep_data[sensor].columns
        ]
        for measure in sensor_measures:
            logger.info(
                "running hodmd pipeline for %s sensor, %s measure", sensor, measure
            )
            data = prep_data[sensor][measure[0]]
            results, timestamps = hodmd_pipeline(
                data.index,
                data.values,
                [data.name],
                save_path=save_path,
                save_suffix="_{0}_{1}".format(sensor, measure[0]),
            )

            measure_values = [
                {
                    "measure_name": measure[0],
                    "values": list(results[0, :]),
                    "timestamps": [t.isoformat() for t in timestamps],
                },
            ]

            response = auth_backend_call(
                "post",
                "/model/insert-model-run",
                {
                    "model_name": "HODMD",
                    "scenario_description": scenario,
                    "measures_and_values": measure_values,
                    "sensor_unique_id": sensor,
                    "sensor_measure": {"name": measure[0], "units": measure[1]},
                },
                token=token,
            )
            if response.status_code != 201:
                raise BackendCallError(response)
            logger.info("Inserted run")


def hodmd_multi_measure(
    prep_data: pd.DataFrame,
    sensor_unique_ids: List[(str | int)],
    measures_list: List[Tuple[str, str]],
    scenario: str,
    save_path: str,
    token: str,
) -> None:
    # loop through every sensor
    for sensor in sensor_unique_ids:
        data = prep_data[sensor]
        # filter measures_list: only retrieve measures related to the current sensor
        sensor_measures = [
            m for m in measures_list if m[0] in prep_data[sensor].columns
        ]
        logger.info("running hodmd pipeline for %s sensor across all measures", sensor)
        results, timestamps = hodmd_pipeline(
            data.index,
            data.values,
            data.columns.tolist(),
            save_path=save_path,
            save_suffix="_{0}".format(sensor),
        )

        # results.shape: (num_sensor_measures, timeseries_predicitons)
        for idx, measure in enumerate(sensor_measures):
            measure_values = [
                {
                    "measure_name": measure[0],
                    "values": results[idx].tolist(),
                    "timestamps": [t.isoformat() for t in timestamps],
                },
            ]

            response = auth_backend_call(
                "post",
                "/model/insert-model-run",
                {
                    "model_name": "HODMD",
                    "scenario_description": scenario,
                    "measures_and_values": measure_values,
                    "sensor_unique_id": sensor,
                    "sensor_measure": {"name": measure[0], "units": measure[1]},
                },
                token=token,
            )
            if response.status_code != 201:
                raise BackendCallError(response)
            logger.info("Inserted run")


def main() -> None:
    run_pipeline()


if __name__ == "__main__":
    main()
