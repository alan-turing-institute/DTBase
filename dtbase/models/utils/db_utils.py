"""
Useful database-related functions for predictive models
"""

import logging
import sys
import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from dtbase.core.db import connect_db, session_open, session_close

from dtbase.core.constants import SQL_CONNECTION_STRING, SQL_DBNAME

logger = logging.getLogger(__name__)


def get_sqlalchemy_session(connection_string=None, dbname=None):
    """
    For other functions in this module, if no session is provided as an argument,
    they will call this to get a session using default connection string.
    """
    if not connection_string:
        connection_string = SQL_CONNECTION_STRING
    if not dbname:
        dbname = SQL_DBNAME
    status, log, engine = connect_db(connection_string, dbname)
    session = session_open(engine)
    return session


def print_rows_head(rows, numrows=0):
    logging.info("Printing:{0} of {1}".format(numrows, len(rows)))
    if numrows == 0:
        for row in rows[: len(rows)]:
            logging.info(row)
    else:
        for row in rows[:numrows]:
            logging.info(row)


def insert_model_run(sensor_id=None, model_id=None, time_forecast=None, session=None):
    if not session:
        session = get_sqlalchemy_session()
    if sensor_id is not None and model_id is not None and time_forecast is not None:
        mr = ModelRunClass(
            sensor_id=sensor_id, model_id=model_id, time_forecast=time_forecast
        )
        try:
            session.add(mr)
            session.commit()
            session.refresh(mr)
            run_id = mr.id
            print(f"Inserted model run {run_id}")
            return run_id
        except exc.SQLAlchemyError:
            session.rollback()
    session.close()


def insert_model_product(run_id=None, measure_id=None, session=None):
    if not session:
        session = get_sqlalchemy_session()
    if run_id is not None and measure_id is not None:
        mp = ModelProductClass(run_id=run_id, measure_id=measure_id)
        try:
            session.add(mp)
            session.commit()
            session.refresh(mp)
            product_id = mp.id
            print(f"Inserting model product {product_id}")
            return product_id
        except exc.SQLAlchemyError:
            session.rollback()
    session.close()


def insert_model_predictions(predictions=None, session=None):
    if not session:
        session = get_sqlalchemy_session()
    num_rows_inserted = 0
    if predictions is not None:
        print(f"Inserting {len(predictions)} model prediction values")
        if len(predictions) > 0:
            for prediction in predictions:
                mv = ModelValueClass(
                    product_id=prediction[0],
                    prediction_value=prediction[1],
                    prediction_index=prediction[2],
                )
                try:
                    session.add(mv)
                    session.commit()
                    num_rows_inserted += 1
                except exc.SQLAlchemyError as e:
                    print(f"Error adding row: {e}")
                    session.rollback()
                    break
    session.close()
    print(f"Inserted {num_rows_inserted} value predictions")
    return num_rows_inserted
