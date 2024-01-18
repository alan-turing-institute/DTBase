"""
A module for keeping track of constants
"""
import logging
import os
from urllib import parse

logging.basicConfig(level=logging.DEBUG)


def make_conn_string(
    sql_engine: str, sql_user: str, sql_password: str, sql_host: str, sql_port: str
) -> str:
    """
    Constructs a connection string.
    Arguments:
        sql_engine
        sql_user
        sql_password
        sql_host
        sql_port

    Returns:
        connection string
    """

    return "%s://%s:%s@%s:%s" % (
        sql_engine,
        sql_user,
        parse.quote(sql_password),
        sql_host,
        sql_port,
    )


# Create connection string
SQL_ENGINE = "postgresql"
SQL_USER = os.environ.get("DT_SQL_USER", "DUMMY").strip()
SQL_PASSWORD = os.environ.get("DT_SQL_PASS", "DUMMY").strip()
SQL_HOST = os.environ.get("DT_SQL_HOST", "DUMMY").strip()
SQL_PORT = os.environ.get("DT_SQL_PORT", "DUMMY").strip()
SQL_CONNECTION_STRING = make_conn_string(
    SQL_ENGINE,
    SQL_USER,
    parse.quote(SQL_PASSWORD),
    SQL_HOST,
    SQL_PORT,
)
SQL_DBNAME = os.environ.get("DT_SQL_DBNAME", "DUMMY").strip().lower()
SQL_DEFAULT_DBNAME = "postgres"
SQL_SSLMODE = "require"

# same for the temporary db used for unit testing
SQL_TEST_USER = os.environ.get("DT_SQL_TESTUSER", "DUMMY").strip()
SQL_TEST_PASSWORD = os.environ.get("DT_SQL_TESTPASS", "DUMMY").strip()
SQL_TEST_HOST = os.environ.get("DT_SQL_TESTHOST", "DUMMY").strip()
SQL_TEST_PORT = os.environ.get("DT_SQL_TESTPORT", "DUMMY").strip()
SQL_TEST_DBNAME = os.environ.get("DT_SQL_TESTDBNAME", "test_db")

SQL_TEST_CONNECTION_STRING = make_conn_string(
    SQL_ENGINE,
    SQL_TEST_USER,
    parse.quote(SQL_TEST_PASSWORD),
    SQL_TEST_HOST,
    SQL_TEST_PORT,
)

# backend API base URL, used by frontend, ingress, and model functions.
CONST_BACKEND_URL = os.environ.get("DT_BACKEND_URL", "http://localhost:5000")

# how many rows to display in tables
CONST_MAX_RECORDS = 50000

CONST_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

DEFAULT_USER_EMAIL = "default_user@localhost"
DEFAULT_USER_PASS = os.environ.get("DT_DEFAULT_USER_PASS", None)

JWT_ACCESS_TOKEN_EXPIRES = int(
    os.environ.get("DT_JWT_ACCESS_TOKEN_EXPIRES_SECONDS", 3600)
)
JWT_REFRESH_TOKEN_EXPIRES = JWT_ACCESS_TOKEN_EXPIRES + 3600
