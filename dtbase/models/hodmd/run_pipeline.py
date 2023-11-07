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
from dtbase.models.hodmd.hodmd_model import hodmd_pipeline
from dtbase.models.utils.config import config
from dtbase.models.utils.dataprocessor.clean_data import clean_data_list
from dtbase.models.utils.dataprocessor.get_data import get_training_data
from dtbase.models.utils.dataprocessor.prepare_data import prepare_data
from dtbase.models.utils.db_utils import get_sqlalchemy_session

logging.getLogger("matplotlib").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def fetch_data():
    # fetch training data from the database
    sensor_data = get_training_data()

    # clean the training data
    cleaned_data = clean_data_list(sensor_data)

    # prepare the clean data for the HODMD model
    prep_data = prepare_data(cleaned_data)

    return prep_data


def run_pipeline(session=None, plots_save_path=None, multi_measure=False) -> None:
    # set up logging
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    field_styles = coloredlogs.DEFAULT_FIELD_STYLES
    field_styles["levelname"][
        "color"
    ] = "yellow"  # change the default levelname color from black to yellow
    coloredlogs.ColoredFormatter(field_styles=field_styles)
    coloredlogs.install(level="INFO")

    prep_data = fetch_data()

    if not session:
        session = get_sqlalchemy_session()

    # ensure we have the Model in the db, or insert if not
    try:
        model_id_from_name("HODMD", session=session)
    except (ValueError):
        # insert the model
        insert_model("HODMD", session=session)

    # ensure we have the model scenario in the db, or insert if not
    try:
        scenario_id_from_description(
            model_name="HODMD", description="BusinessAsUsual", session=session
        )
    except (ValueError):
        insert_model_scenario(
            model_name="HODMD", description="BusinessAsUsual", session=session
        )

    # ensure that we have all measures in the database, or insert if not
    measures_list = config(section="sensors")["include_measures"]

    db_measures = list_model_measures(session=session)
    db_measure_names = [m["name"] for m in db_measures]
    for measure in measures_list:
        if measure[0] not in db_measure_names:
            insert_model_measure(measure[0], measure[1], "float", session=session)

    session.commit()

    # run the HODMD pipeline for every sensor
    sensor_unique_ids = config(section="sensors")["include_sensors"]

    # run HODMD pipeline
    if multi_measure:
        hodmd_multi_measure(
            session, prep_data, sensor_unique_ids, measures_list, plots_save_path
        )
    else:
        hodmd_single_measure(
            session, prep_data, sensor_unique_ids, measures_list, plots_save_path
        )


def hodmd_single_measure(
    session, prep_data, sensor_unique_ids, measures_list, save_path
):
    # loop through every sensor
    for sensor in sensor_unique_ids:
        session.begin()
        sensor_id = sensor_id_from_unique_identifier(
            unique_identifier=sensor, session=session
        )
        # filter measures_list: only retrieve measures related to the current sensor
        sensor_measures = [
            m for m in measures_list if m[0] in prep_data[sensor].columns
        ]
        for measure in sensor_measures:
            logger.info(
                "running hodmd pipeline for %s sensor, %s measure", sensor, measure
            )
            sensor_measure_id = measure_id_from_name_and_units(
                measure[0], measure[1], session=session
            )
            data = prep_data[sensor][measure]
            results, timestamps = hodmd_pipeline(
                data.index,
                data.values,
                [
                    data.name,
                ],
                save_path=save_path,
                save_suffix="_{0}_{1}".format(sensor, measure[0]),
            )

            measure_values = [
                {
                    "measure_name": measure[0],
                    "values": list(results),
                    "timestamps": list(timestamps),
                },
            ]
            try:
                insert_model_run(
                    model_name="HODMD",
                    scenario_description="BusinessAsUsual",
                    measures_and_values=measure_values,
                    sensor_id=sensor_id,
                    sensor_measure_id=sensor_measure_id,
                    session=session,
                )
                session.commit()
            except Exception:
                # TODO We should log a warning here.
                session.rollback()
                session.close()
        session.close()


def hodmd_multi_measure(
    session, prep_data, sensor_unique_ids, measures_list, save_path
):
    # loop through every sensor
    for sensor in sensor_unique_ids:
        session.begin()
        sensor_id = sensor_id_from_unique_identifier(
            unique_identifier=sensor, session=session
        )
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
                    "timestamps": list(timestamps),
                },
            ]
            try:
                run_id = insert_model_run(
                    model_name="HODMD",
                    scenario_description="BusinessAsUsual",
                    measures_and_values=measure_values,
                    sensor_id=sensor_id,
                    sensor_measure_id=measure_id_from_name_and_units(
                        measure[0], measure[1], session=session
                    ),
                    session=session,
                )
                session.commit()
                logger.info(f"Inserted model run {run_id}")
            except Exception as e:
                logger.info(f"Problem inserting model run: {e}")
                session.rollback()
                session.close()
        session.close()


def main() -> None:
    run_pipeline()


if __name__ == "__main__":
    main()
