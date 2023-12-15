#!/usr/bin/env python
import logging
import os
import sys
from collections import defaultdict

import coloredlogs

from dtbase.models.arima.arima.arima_pipeline import arima_pipeline
from dtbase.models.utils.config import config
from dtbase.models.utils.dataprocessor.clean_data import clean_data
from dtbase.models.utils.dataprocessor.get_data import get_training_data
from dtbase.models.utils.dataprocessor.prepare_data import prepare_data

OUTPUT_DIR = os.path.join(os.getcwd(), "results")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def main() -> None:
    # set up logging
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    field_styles = coloredlogs.DEFAULT_FIELD_STYLES
    field_styles["levelname"][
        "color"
    ] = "yellow"  # change the default levelname color from black to yellow
    coloredlogs.ColoredFormatter(field_styles=field_styles)
    coloredlogs.install(level="INFO")

    # fetch training data from the database
    sensor_data = get_training_data()

    # clean the training data
    cleaned_data = clean_data(sensor_data[0])

    # prepare the clean data for the ARIMA model
    prep_data = prepare_data(cleaned_data)

    # run the ARIMA pipeline for every temperature sensor
    sensor_ids = config(section="sensors")["include_sensors"]
    measures = config(section="sensors")["include_measures"]
    forecast_results = defaultdict(dict)

    # loop through every sensor/measure

    for sensor in sensor_ids:
        for measure_name, measure_units in measures:
            key = sensor + "_" + measure_name
            values = prep_data[sensor][measure_name]
            # save 10% of the data for testing
            n_samples = len(values)
            values = values.iloc[: int(0.9 * n_samples)]
            mean_forecast, conf_int, metrics = arima_pipeline(values)
            forecast_results[key]["mean_forecast"] = mean_forecast
            forecast_results[key]["conf_int"] = conf_int
            forecast_results[key]["metrics"] = metrics
            # save to disk
            conf_int["mean_forecast"] = mean_forecast
            conf_int["sensor"] = sensor
            conf_int["measure"] = measure_name
            conf_int.to_csv(os.path.join(OUTPUT_DIR, f"{key}.csv"))


if __name__ == "__main__":
    main()
