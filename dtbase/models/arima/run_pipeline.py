#!/usr/bin/env python
import os
import sys
from collections import defaultdict
import pandas as pd
import logging, coloredlogs


from dtbase.core.models import (
    list_model_measures,
    list_model_scenarios,
    insert_model_run,
    insert_model_product,
    insert_model_measure,
    insert_model_scenario,
    insert_model,
    model_id_from_name,
    scenario_id_from_description,
)
from dtbase.core.sensors import (
    measure_id_from_name_and_units,
    sensor_id_from_unique_identifier,
)
from dtbase.models.utils.db_utils import (
    get_sqlalchemy_session,
)
from dtbase.models.utils.dataprocessor.get_data import get_training_data
from dtbase.models.utils.dataprocessor.clean_data import clean_data
from dtbase.models.utils.dataprocessor.prepare_data import prepare_data
from dtbase.models.utils.config import config
from dtbase.models.arima.arima.arima_pipeline import arima_pipeline


def run_pipeline(session=None) -> None:
    # set up logging
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    field_styles = coloredlogs.DEFAULT_FIELD_STYLES
    coloredlogs.ColoredFormatter(field_styles=field_styles)
    coloredlogs.install(level="INFO")

    # fetch training data from the database
    sensor_data = get_training_data()

    # clean the training data
    cleaned_data = clean_data(sensor_data[0])

    # prepare the clean data for the ARIMA model
    prep_data = prepare_data(cleaned_data)

    if not session:
        session = get_sqlalchemy_session()
    # ensure we have the Model in the db, or insert if not
    model_id = None
    try:
        model_id = model_id_from_name("Arima", session=session)
    except (ValueError):
        # insert the model
        m = insert_model("Arima", session=session)
        model_id = m.id

    # ensure we have the model scenario in the db, or insert if not
    scenario_id = None
    try:
        scenario_id = scenario_id_from_description(
            model_name="Arima", description="BusinessAsUsual", session=session
        )
    except (ValueError):
        ms = insert_model_scenario(
            model_name="Arima", description="BusinessAsUsual", session=session
        )
        scenario_id = ms.id

    # ensure that we have all measures in the database, or insert if not
    base_measures_list = config(section="sensors")["include_measures"]

    db_measures = list_model_measures(session=session)
    db_measure_names = [m["name"] for m in db_measures]
    # base_measures_list will be a list of tuples (measure_name, units)
    for base_measure in base_measures_list:
        for m in ["Mean ", "Upper Bound ", "Lower Bound "]:
            measure = m + base_measure[0]
            if not measure in db_measure_names:
                insert_model_measure(measure, "", "float", session=session)

    session.commit()
    # run the ARIMA pipeline for every sensor
    sensor_unique_ids = list(prep_data.keys())
    # loop through every sensor
    for sensor in sensor_unique_ids:
        session.begin()
        sensor_id = sensor_id_from_unique_identifier(
            unique_identifier=sensor, session=session
        )
        for base_measure in base_measures_list:
            sensor_measure_id = measure_id_from_name_and_units(
                base_measure[0], base_measure[1], session=session
            )
            values = prep_data[sensor][base_measure[0]]
            mean_forecast, conf_int, metrics = arima_pipeline(values)
            mean = {
                "measure_name": "Mean " + base_measure[0],
                "values": list(mean_forecast),
                "timestamps": list(mean_forecast.index),
            }
            upper = {
                "measure_name": "Upper Bound " + base_measure[0],
                "values": list(conf_int.mean_ci_upper),
                "timestamps": list(conf_int.index),
            }
            lower = {
                "measure_name": "Lower Bound " + base_measure[0],
                "values": list(conf_int.mean_ci_lower),
                "timestamps": list(conf_int.index),
            }
            measures_values = [mean, upper, lower]
            try:
                run_id = insert_model_run(
                    model_name="Arima",
                    scenario_description="BusinessAsUsual",
                    measures_and_values=measures_values,
                    sensor_id=sensor_id,
                    sensor_measure_id=sensor_measure_id,
                    session=session,
                )

                session.commit()

            except:
                session.rollback()
                session.close()
        session.close()


def main() -> None:
    run_pipeline()


if __name__ == "__main__":
    main()
