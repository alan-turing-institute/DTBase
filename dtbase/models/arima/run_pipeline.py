#!/usr/bin/env python
import logging
import sys

import coloredlogs

from dtbase.core.models import (
    insert_model,
    insert_model_measure,
    insert_model_run,
    insert_model_scenario,
    list_model_measures,
    model_id_from_name,
    scenario_id_from_description,
)
from dtbase.core.sensors import (
    measure_id_from_name_and_units,
    sensor_id_from_unique_identifier,
)
from dtbase.models.arima.arima.arima_pipeline import arima_pipeline
from dtbase.models.utils.config import config
from dtbase.models.utils.dataprocessor.clean_data import clean_data_list
from dtbase.models.utils.dataprocessor.get_data import get_training_data
from dtbase.models.utils.dataprocessor.prepare_data import prepare_data
from dtbase.models.utils.db_utils import get_sqlalchemy_session

logger = logging.getLogger(__name__)


def run_pipeline(session=None) -> None:
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
    cleaned_data = clean_data_list(sensor_data)

    # prepare the clean data for the ARIMA model
    prep_data = prepare_data(cleaned_data)

    if not session:
        session = get_sqlalchemy_session()
    # ensure we have the Model in the db, or insert if not
    model_id = None
    try:
        model_id = model_id_from_name("Arima", session=session)
        logging.info(f"Found existing model id {model_id} in database")
    except (ValueError):
        # insert the model
        m = insert_model("Arima", session=session)
        model_id = m.id
        logging.info(f"Adding model id {model_id} to database")

    # ensure we have the model scenario in the db, or insert if not
    scenario_id = None
    try:
        scenario_id = scenario_id_from_description(
            model_name="Arima", description="BusinessAsUsual", session=session
        )
        logging.info(f"Found existing scenario id {scenario_id} in database")
    except (ValueError):
        ms = insert_model_scenario(
            model_name="Arima", description="BusinessAsUsual", session=session
        )
        scenario_id = ms.id
        logging.info(f"Adding scenario id {scenario_id} to database")

    # ensure that we have all measures in the database, or insert if not
    base_measures_list = config(section="sensors")["include_measures"]

    db_measures = list_model_measures(session=session)
    db_measure_names = [m["name"] for m in db_measures]
    logging.info(f"measures to use: {base_measures_list}")
    # base_measures_list will be a list of tuples (measure_name, units)
    for base_measure in base_measures_list:
        for m in ["Mean ", "Upper Bound ", "Lower Bound "]:
            measure = m + base_measure[0]
            if measure not in db_measure_names:
                insert_model_measure(measure, "", "float", session=session)
                logging.info(f"Inserting measure {measure} to db")
    session.commit()
    # run the ARIMA pipeline for every sensor
    sensor_unique_ids = list(prep_data.keys())
    logging.info(f"Will look at sensors {sensor_unique_ids}")
    # loop through every sensor
    for sensor in sensor_unique_ids:
        session.begin()
        sensor_id = sensor_id_from_unique_identifier(
            unique_identifier=sensor, session=session
        )
        # filter measures_list: only retrieve measures related to the current sensor
        #        base_measures_list_ = set(base_measures_list).intersection(
        #            set(prep_data[sensor].columns)
        #        )
        base_measures_list = [
            b for b in base_measures_list if b[0] in prep_data[sensor].columns
        ]
        for base_measure in base_measures_list:
            sensor_measure_id = measure_id_from_name_and_units(
                base_measure[0], base_measure[1], session=session
            )
            values = prep_data[sensor][base_measure[0]]
            logger.info(
                "running arima pipeline for %s sensor, %s measure",
                sensor,
                base_measure[0],
            )
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
                logger.info(f"Inserted run {run_id}")
            except Exception as e:
                session.rollback()
                session.close()
                logger.info(f"Problem inserting model run: {e}")
        session.close()


def main() -> None:
    run_pipeline()


if __name__ == "__main__":
    main()
