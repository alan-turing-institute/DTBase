"""
Module for the main functions to create a new database with SQLAlchemy and Postgres,
drop database, and check its structure.
"""

from typing import Literal, Tuple

import sqlalchemy as sqla
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import RelationshipProperty, Session, sessionmaker
from sqlalchemy_utils import database_exists, drop_database

from dtbase.core.constants import SQL_DEFAULT_DBNAME
from dtbase.core.exc import DatabaseConnectionError
from dtbase.core.structure import BASE


def create_tables(engine: Engine) -> None:
    """Create all the tables for the database."""
    BASE.metadata.create_all(engine)


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
        raise DatabaseConnectionError("Cannot find db: %s")
    try:
        engine = sqla.create_engine(db_conn_string, pool_size=20, max_overflow=-1)
    except SQLAlchemyError:
        raise DatabaseConnectionError("Cannot connect to db: %s" % db_name)
    return engine


def drop_tables(engine: Engine) -> None:
    """Drop all tables in the database."""
    BASE.metadata.drop_all(engine)


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


def check_database_structure(
    engine: Engine,
) -> Tuple[Literal[False], str] | Tuple[Literal[True], None]:
    """
    Check whether the current database matches the models declared in model base.

    Currently we check that all tables exist with all columns. What is not checked
    * Column types are not verified
    * Relationships are not verified

    engine: The db engine

    return: True, None if all declared models have corresponding tables and columns.
    """

    # Accesses sql db
    iengine = sqla.inspect(engine)

    # gets table names from sql server in python list
    sql_tables = iengine.get_table_names()

    if sql_tables:
        # goes through the sqlalchemy classes
        for _, sql_class in BASE.registry._class_registry.items():
            try:
                tablename = sql_class.__tablename__
            except AttributeError:
                # This mostly catches the case of _ModuleMarker, which isn't an actual
                # class we are interested in.
                continue

            # checks if all tablenames in class exist in sql
            if tablename in sql_tables:
                # gets the column names of each table in sql
                columns = [c["name"] for c in iengine.get_columns(tablename)]

                # gets objects in each class in the form of:
                # Readings_Advanticsys.sensor_relationship
                mapper = sqla.inspect(sql_class)

                for obj in mapper.attrs:
                    # checks if the object is a relationship
                    if isinstance(obj, RelationshipProperty):
                        # To do add checks for relations
                        pass
                    else:
                        # assume normal flat column
                        if obj.key not in columns:
                            return (
                                False,
                                "Model %s declares column %s which\
                            does not exist"
                                % (sql_class, columns.key),
                            )
            else:
                return (
                    False,
                    "Model %s declares table %s which doesn't exist"
                    % (sql_class, tablename),
                )

    else:
        return False, "No tables found in the db"

    return True, None


def session_open(engine: Engine) -> Session:
    """
    Opens a new connection/session to the db and binds the engine
    -engine: the connected engine
    """
    Session = sessionmaker()
    Session.configure(bind=engine)
    return Session()


def session_close(session: Session) -> None:
    """
    Closes the current open session
    -session: an open session
    """
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
