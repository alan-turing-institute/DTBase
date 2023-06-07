#!/usr/bin/env python
import logging
logging.getLogger('matplotlib').setLevel(logging.WARNING)

import sys
from collections import defaultdict
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
from dtbase.core.sensors import measure_id_from_name, sensor_id_from_unique_identifier
from dtbase.models.utils.db_utils import (
    get_sqlalchemy_session,
)
from dtbase.models.utils.dataprocessor.get_data import get_training_data
from dtbase.models.utils.dataprocessor.clean_data import clean_data, clean_data_list
from dtbase.models.utils.dataprocessor.prepare_data import prepare_data
from dtbase.models.utils.config import config
from dtbase.models.hodmd.hodmd_model import hodmd_pipeline

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
    model_id = None
    try:
        model_id = model_id_from_name("HODMD", session=session)
    except (ValueError):
        # insert the model
        m = insert_model("HODMD", session=session)
        model_id = m.id

    # ensure we have the model scenario in the db, or insert if not
    scenario_id = None
    try:
        scenario_id = scenario_id_from_description(
            model_name="HODMD", description="BusinessAsUsual", session=session
        )
    except (ValueError):
        ms = insert_model_scenario(
            model_name="HODMD", description="BusinessAsUsual", session=session
        )
        scenario_id = ms.id

    # ensure that we have all measures in the database, or insert if not
    measures_list = config(section="sensors")["include_measures"]
    db_measures = list_model_measures(session=session)
    db_measure_names = [m["name"] for m in db_measures]
    for measure in measures_list:
        if not measure in db_measure_names:
            insert_model_measure(measure, "", "float", session=session)

    session.commit()

    # run the HODMD pipeline for every sensor
    sensor_unique_ids = config(section="sensors")["include_sensors"]

    # run HODMD pipeline
    if multi_measure:
        hodmd_multi_measure(session, prep_data, sensor_unique_ids, measures_list, plots_save_path)
    else:
        hodmd_single_measure(session, prep_data, sensor_unique_ids, measures_list, plots_save_path)


def hodmd_single_measure(session, prep_data, sensor_unique_ids, measures_list, save_path):
    # loop through every sensor
    for sensor in sensor_unique_ids:
        session.begin()
        sensor_id = sensor_id_from_unique_identifier(
            unique_identifier=sensor, session=session
        )
        # filter measures_list: only retrieve measures related to the current sensor
        sensor_measures = set(measures_list).intersection(set(prep_data[sensor].columns))
        for measure in sensor_measures:
            logger.info('running hodmd pipeline for %s sensor, %s measure', sensor, measure)
            sensor_measure_id = measure_id_from_name(measure, session=session)
            data = prep_data[sensor][measure]
            results, timestamps = hodmd_pipeline(data.index, data.values, [data.name, ], \
                save_path=save_path, save_suffix='_{0}_{1}'.format(sensor, measure))

            measure_values = [
                {
                    "measure_name": measure,
                    "values": list(results),
                    "timestamps": list(timestamps),
                },
            ]
            try:
                run_id = insert_model_run(
                    model_name="HODMD",
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

def hodmd_multi_measure(session, prep_data, sensor_unique_ids, measures_list, save_path):
    # loop through every sensor
    for sensor in sensor_unique_ids:
        session.begin()
        sensor_id = sensor_id_from_unique_identifier(
            unique_identifier=sensor, session=session
        )
        data = prep_data[sensor]
        # filter measures_list: only retrieve measures related to the current sensor
        sensor_measures = set(measures_list).intersection(set(data.columns))

        logger.info('running hodmd pipeline for %s sensor across all measures', sensor)
        results, timestamps = hodmd_pipeline(data.index, data.values, data.columns.tolist(), \
            save_path=save_path, save_suffix='_{0}'.format(sensor))

        # results.shape: (num_sensor_measures, timeseries_predicitons)
        for idx, measure in enumerate(sensor_measures):
            measure_values = [
                {
                    "measure_name": measure,
                    "values": list(results[idx]),
                    "timestamps": list(timestamps),
                },
            ]
            try:
                run_id = insert_model_run(
                    model_name="HODMD",
                    scenario_description="BusinessAsUsual",
                    measures_and_values=measures_values,
                    sensor_id=sensor_id,
                    sensor_measure_id=measure_id_from_name(measure, session=session),
                    session=session,
                )
                session.commit()
            except:
                session.rollback()
                session.close()
        session.close()


def main() -> None:
    run_pipeline()

if __name__ == '__main__':
    main()
