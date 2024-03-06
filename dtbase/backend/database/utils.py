"""
Module for the main functions to create a new database with SQLAlchemy and Postgres,
drop database, and check its structure.
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Generator, Optional

import sqlalchemy as sqla
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session as SqlaSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy_utils import database_exists, drop_database

from dtbase.backend.database.structure import (
    Base,
    LocationBooleanValue,
    LocationFloatValue,
    LocationIntegerValue,
    LocationStringValue,
    ModelBooleanValue,
    ModelFloatValue,
    ModelIntegerValue,
    ModelStringValue,
    SensorBooleanReading,
    SensorFloatReading,
    SensorIntegerReading,
    SensorStringReading,
)
from dtbase.backend.exc import DatabaseConnectionError
from dtbase.core.constants import (
    SQL_DEFAULT_DBNAME,
)

# We may have to deal with various objects that represent a database connection session,
# so make a union type of all of them. This is used for type annotations around the
# codebase.
Session = scoped_session[SqlaSession] | SqlaSession

# These are the global database connection objects. They start out being None, since we
# don't want simply importing this module to create a database connection. One is
# expected to call create_global_database_connection to set these up, and then access
# them with global_session_maker and global_engine.
DB_ENGINE: Optional[Engine] = None
DB_SESSION_MAKER: Optional[sessionmaker] = None


def create_global_database_connection(
    connection_string: str, database_name: str, reset: bool = False
) -> None:
    """Create a global database connection.

    This function modifies the global variables DB_ENGINE and DB_SESSION_MAKER, and
    returns nothing.

    Args:
        connection_string (str): The database connection string.
        database_name (str): The name of the database to connect to.
        reset (bool, optional): If True, reset the global database connection even if it
        already exists. Defaults to False.

    Returns:
        None
    """

    global DB_ENGINE, DB_SESSION_MAKER
    if DB_ENGINE is None or reset:
        DB_ENGINE = connect_db(connection_string, database_name)
    if DB_SESSION_MAKER is None or reset:
        DB_SESSION_MAKER = sessionmaker(
            autocommit=False, autoflush=False, bind=DB_ENGINE
        )


def global_session_maker() -> sessionmaker:
    """Get the global database session maker.

    If the global session maker is not set, raise a ValueError.
    """
    if DB_SESSION_MAKER is None:
        raise ValueError(
            "DB_SESSION_MAKER is not set. "
            "You may need to run create_global_database_connection."
        )
    return DB_SESSION_MAKER


def global_engine() -> Engine:
    """Get the global database engine.

    If the global engine is not set, raise a ValueError.
    """
    if DB_ENGINE is None:
        raise ValueError(
            "DB_ENGINE is not set. "
            "You may need to run create_global_database_connection."
        )
    return DB_ENGINE


def db_session() -> Generator[Session, None, None]:
    """Yield a database session to the global database connection.

    This function is used extensively as a FastAPI dependency by any endpoint that needs
    to access the database.

    Raises a ValueError if the global database connection is not set.
    """
    session_maker = global_session_maker()
    with session_maker() as session:
        yield session


def create_tables(engine: Engine) -> None:
    """Create all the tables for the database."""
    Base.metadata.create_all(engine)


def create_database(conn_string: str, db_name: str) -> None:
    """
    Function to create a new database
    -sql_connection_string: a string that holds an address to the db
    -dbname: name of the db (string)
    return: None
    raise: DatabaseConnectionError or SQLAlchemyError if creating the database fails
    """

    # Create connection string
    db_conn_string = "{}/{}".format(conn_string, db_name)

    if database_exists(db_conn_string):
        return
    # Create a new database. On postgres, the postgres database is normally present by
    # default. Connecting as a superuser (eg, postgres), allows to connect and create a
    # new db.
    def_engine = sqla.create_engine(
        "{}/{}".format(conn_string, SQL_DEFAULT_DBNAME),
        pool_size=20,
        max_overflow=-1,
    )

    # You cannot use engine.execute() directly, because postgres does not allow to
    # create databases inside transactions, inside which sqlalchemy always tries to
    # run queries. To get around this, get the underlying connection from the
    # engine:
    with def_engine.connect() as conn:
        # But the connection will still be inside a transaction, so you have to end
        # the open transaction with a commit:
        conn.execute(sqla.text("commit"))

        # Then proceed to create the database using the PostgreSQL command.
        conn.execute(sqla.text("create database " + db_name))

        # Connects to the engine using the new database url
        engine = connect_db(conn_string, db_name)
        # Adds the tables and columns from the classes in module structure
        create_tables(engine)


def connect_db(conn_string: str, db_name: str) -> Engine:
    """
    Function to connect to a database
    -conn_string: the string that holds the connection to postgres
    -dbname: name of the database
    return: engine: returns the engine object
    raises: DatabaseConnectionError if connecting fails
    """

    # Create connection string
    db_conn_string = "{}/{}".format(conn_string, db_name)

    # Connect to an engine
    if not database_exists(db_conn_string):
        raise DatabaseConnectionError("Cannot find db: %s", db_conn_string)
    try:
        engine = sqla.create_engine(db_conn_string, pool_size=20, max_overflow=-1)
    except SQLAlchemyError:
        raise DatabaseConnectionError("Cannot connect to db: %s" % db_name)
    return engine


def drop_tables(engine: Engine) -> None:
    """Drop all tables in the database."""
    Base.metadata.drop_all(engine)


def drop_db(conn_string: str, db_name: str) -> None:
    """
    Function to drop db
    *What it doesnt do: drop individual table/column/values
    -conn_string: the string that holds the connection to postgres
    -dbname: name of the database
    return: None
    raise: SQLAlchemyError if dropping the database fails
    """

    # Connection string
    db_conn_string = "{}/{}".format(conn_string, db_name)

    if database_exists(db_conn_string):
        # Connect to the db
        engine = connect_db(conn_string, db_name)

        # Disconnects all users from the db we want to drop
        connection = engine.connect()
        connection.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        version = connection.dialect.server_version_info
        pid_column = "pid" if (version >= (9, 2)) else "procpid"
        text = """
        SELECT pg_terminate_backend(pg_stat_activity.%(pid_column)s)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = '%(database)s'
          AND %(pid_column)s <> pg_backend_pid();
        """ % {
            "pid_column": pid_column,
            "database": db_name,
        }
        connection.execute(sqla.text(text))

        # Drops db
        drop_database(db_conn_string)


def row_mappings_to_dicts(rows: Sequence[RowMapping]) -> list[dict]:
    """Convert the list of RowMappings that SQLAlchemy's mappings() returns into plain
    dicts.
    """
    return [{k: v for k, v in row.items()} for row in rows]


location_value_class_dict = {
    bool: LocationBooleanValue,
    float: LocationFloatValue,
    int: LocationIntegerValue,
    str: LocationStringValue,
    "boolean": LocationBooleanValue,
    "float": LocationFloatValue,
    "integer": LocationIntegerValue,
    "string": LocationStringValue,
}


model_value_class_dict = {
    bool: ModelBooleanValue,
    float: ModelFloatValue,
    int: ModelIntegerValue,
    str: ModelStringValue,
    "boolean": ModelBooleanValue,
    "float": ModelFloatValue,
    "integer": ModelIntegerValue,
    "string": ModelStringValue,
}


sensor_reading_class_dict = {
    bool: SensorBooleanReading,
    float: SensorFloatReading,
    int: SensorIntegerReading,
    str: SensorStringReading,
    "boolean": SensorBooleanReading,
    "float": SensorFloatReading,
    "integer": SensorIntegerReading,
    "string": SensorStringReading,
}


def check_datatype(value: str, datatype_name: str) -> bool:
    if datatype_name == "string":
        return isinstance(value, str)
    if datatype_name == "integer":
        return isinstance(value, int)
    if datatype_name == "float":
        return isinstance(value, float)
    if datatype_name == "boolean":
        return isinstance(value, bool)
    raise ValueError(f"Unrecognised datatype: {datatype_name}")
