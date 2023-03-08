"""
Utilities (miscellaneous routines) module
"""
from datetime import datetime, timedelta
import io
import json
import logging
import uuid

from flask import send_file
import pandas as pd
from sqlalchemy import exc

from dtbase.core.db import connect_db, session_open, session_close
from dtbase.core.constants import SQL_CONNECTION_STRING, SQL_DBNAME
from dtbase.core.structure import User
from dtbase.core.structure import SQLA as db

from dtbase.core.structure import (
    Location,
    LocationBooleanValue,
    LocationFloatValue,
    LocationIdentifier,
    LocationIntegerValue,
    LocationSchema,
    LocationSchemaIdentifierRelation,
    LocationStringValue,
)

def get_db_session(return_engine=False):
    """
    Get an SQLAlchemy session on the database.

    Log an error message an return None if the connection fails.

    Parameters
    ==========
    return_engine: bool, if True return the sqlalchmy engine as well as session

    Returns
    =======
    session: SQLAlchemy session object
    engine (optional): SQLAlchemy engine
    """
    success, log, engine = connect_db(SQL_CONNECTION_STRING, SQL_DBNAME)
    if not success:
        logging.error(log)
        return None
    session = session_open(engine)
    if return_engine:
        return session, engine
    else:
        return session


def query_result_to_array(query_result, date_iso=True):
    """
    Forms an array of ResultProxy results.
    Args:
        query_result: a ResultProxy representing results of the sql alchemy query
        execution
    Returns:
        results_arr: an array with ResultProxy results
    """

    dict_entry, results_arr = {}, []

    for rowproxy in query_result:

        # NOTE: added ._asdict() as rowproxy didnt come in the form of dict and could
        # not read .items.
        if "_asdict" in dir(rowproxy):
            rowproxy = rowproxy._asdict()
        elif "_mapping" in dir(rowproxy):
            rowproxy = rowproxy._mapping
        else:
            pass

        for column, value in rowproxy.items():

            if isinstance(value, datetime):
                if date_iso:
                    dict_entry = {**dict_entry, **{column: value.isoformat()}}
                else:
                    dict_entry = {
                        **dict_entry,
                        **{column: value.replace(microsecond=0)},
                    }
            else:
                dict_entry = {**dict_entry, **{column: value}}
        results_arr.append(dict_entry)

    return results_arr


def query_result_to_dict(query_result, date_iso=True):
    """
    If we have a single query result, return output as a dict rather than a list
    Args:
        query_result: a ResultProxy representing results of the sql alchemy query
        execution
    Returns:
        results_dict: a dict containing the results
    """
    if len(query_result) != 1:
        print("Only call query_result_to_dict if we have a single result.")
        return {}
    rowproxy = query_result[0]
    dict_entry = {}
    if "_asdict" in dir(rowproxy):
        rowproxy = rowproxy._asdict()
    for column, value in rowproxy.items():
        if isinstance(value, datetime):
            if date_iso:
                dict_entry = {**dict_entry, **{column: value.isoformat()}}
            else:
                dict_entry = {
                    **dict_entry,
                    **{column: value.replace(microsecond=0)},
                }
        else:
            dict_entry = {**dict_entry, **{column: value}}
    return dict_entry


def jsonify_query_result(query_result):
    """
    Jasonifies ResultProxy results.

    Args:
        query_result: a ResultProxy representing results of the sql alchemy query
        execution
    Returns:
        result: jsonified result of the query_result
    """

    results_arr = query_result_to_array(query_result)

    # extend the JSONEncode to deal with UUID objects
    class UUIDEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, uuid.UUID):
                return str(obj)
            return json.JSONEncoder.default(self, obj)

    result = json.dumps(
        results_arr, ensure_ascii=True, indent=4, sort_keys=True, cls=UUIDEncoder
    )

    return result


def get_default_datetime_range():
    """
    Returns a default datetime range (7 days): dt_from, dt_to
    """

    time_delta = -7

    dt_to = (
        datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        + timedelta(days=1)
        + timedelta(milliseconds=-1)
    )

    dt_from = (dt_to + timedelta(time_delta)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    return dt_from, dt_to


def parse_date_range_argument(request_args):
    """
    Parses date range arguments from the request_arguments string.

    Arguments:
        request_args - request arguments as a string
        arg - argument to be extracted from the request arguments

    Returns:
        tuple of two datetime objects
    """

    if request_args is None:
        return get_default_datetime_range()

    try:
        dt_to = (
            datetime.strptime(request_args.split("-")[1], "%Y%m%d").replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            + timedelta(days=1)
            + timedelta(milliseconds=-1)
        )

        dt_from = datetime.strptime(request_args.split("-")[0], "%Y%m%d").replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        return dt_from, dt_to

    except ValueError:
        return get_default_datetime_range()


def create_user(username, email, password):
    """Create a new user.

    Return (True, user_id) if successful, (False, error_message) if not.
    """
    try:
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return True, user.id
    except exc.SQLAlchemyError as e:
        db.session.rollback()
        return False, str(e)


def delete_user(username, email):
    """Delete the user with this username and email.

    Return (True, user_id) if successful, (False, error_message) if not.
    """
    try:
        user = User.query.filter_by(username=username, email=email).first()
        db.session.delete(user)
        db.session.flush()
        db.session.commit()
        return True, user.id
    except exc.SQLAlchemyError as e:
        db.session.rollback()
        return False, str(e)


def change_user_password(username, email, password):
    """Change the password of a given user.

    Return (True, user_id) if successful, (False, error_message) if not.
    """
    try:
        user = User.query.filter_by(username=username, email=email).first()
        old_hashed_password = user.password
        user.password = password
        new_hashed_password = user.password
        if old_hashed_password != new_hashed_password:
            db.session.flush()
            db.session.commit()
            return True, user.id
        else:
            return False, f"Password already up-to-date for {username}"
    except exc.SQLAlchemyError as e:
        db.session.rollback()
        return False, str(e)


def insert_to_db_from_df(engine, df, DbClass):
    """
    Read a CSV file into a pandas dataframe, and then upload to
    database table

    Parameters
    ==========
    engine: SQL engine object
    df:pandas.DataFrame, input data
    DbClass:class from core.structure.py
    """
    assert not df.empty

    # Creates/Opens a new connection to the db and binds the engine
    session = session_open(engine)

    # Check if table is empty and bulk inserts if it is
    first_entry = session.query(DbClass).first()

    if first_entry is None:
        session.bulk_insert_mappings(DbClass, df.to_dict(orient="records"))
        session_close(session)
        assert session.query(DbClass).count() == len(df.index)
    else:
        records = df.to_dict(orient="records")
        for record in records:
            try:
                session.add(DbClass(**record))
                session.commit()
            except exc.SQLAlchemyError as e:
                session.rollback()
    session_close(session)
    print(f"Inserted {len(df.index)} rows to table {DbClass.__tablename__}")


def get_value_class_from_instance_type(value):
    value_class = (
        LocationBooleanValue
        if isinstance(value, bool)
        else LocationFloatValue
        if isinstance(value, float)
        else LocationIntegerValue
        if isinstance(value, int)
        else LocationStringValue
        if isinstance(value, str)
        else None
    )
    return value_class


def get_value_class_from_type_name(name):
    value_class = (
        LocationBooleanValue
        if name == "bool"
        else LocationFloatValue
        if name == "float"
        else LocationIntegerValue
        if name == "int"
        else LocationStringValue
        if name == "string"
        else None
    )
    return value_class
