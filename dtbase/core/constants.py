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
SQL_USER = os.environ["DT_SQL_USER"].strip() if "DT_SQL_USER" in os.environ else "DUMMY"
SQL_PASSWORD = (
    os.environ["DT_SQL_PASS"].strip() if "DT_SQL_PASS" in os.environ else "DUMMY"
)
SQL_HOST = os.environ["DT_SQL_HOST"].strip() if "DT_SQL_HOST" in os.environ else "DUMMY"
SQL_PORT = os.environ["DT_SQL_PORT"].strip() if "DT_SQL_PORT" in os.environ else "DUMMY"
SQL_CONNECTION_STRING = make_conn_string(
    SQL_ENGINE,
    SQL_USER,
    parse.quote(SQL_PASSWORD),
    SQL_HOST,
    SQL_PORT,
)
SQL_DBNAME = (
    os.environ["DT_SQL_DBNAME"].strip().lower()
    if "DT_SQL_DBNAME" in os.environ
    else "DUMMY"
)
SQL_DEFAULT_DBNAME = "postgres"
SQL_SSLMODE = "require"

# same for the temporary db used for unit testing
SQL_TEST_USER = (
    os.environ["DT_SQL_TESTUSER"].strip()
    if "DT_SQL_TESTUSER" in os.environ
    else "DUMMY"
)
SQL_TEST_PASSWORD = (
    os.environ["DT_SQL_TESTPASS"].strip()
    if "DT_SQL_TESTPASS" in os.environ
    else "DUMMY"
)
SQL_TEST_HOST = (
    os.environ["DT_SQL_TESTHOST"].strip()
    if "DT_SQL_TESTHOST" in os.environ
    else "DUMMY"
)
SQL_TEST_PORT = (
    os.environ["DT_SQL_TESTPORT"].strip()
    if "DT_SQL_TESTPORT" in os.environ
    else "DUMMY"
)
SQL_TEST_DBNAME = (
    os.environ["DT_SQL_TESTDBNAME"] if "DT_SQL_TESTDBNAME" in os.environ else "test_db"
)

SQL_TEST_CONNECTION_STRING = make_conn_string(
    SQL_ENGINE,
    SQL_TEST_USER,
    parse.quote(SQL_TEST_PASSWORD),
    SQL_TEST_HOST,
    SQL_TEST_PORT,
)

# backend API base URL, used by frontend, ingress, and model functions.
CONST_BACKEND_URL = (
    os.environ["DT_BACKEND_URL"]
    if "DT_BACKEND_URL" in os.environ
    else "http://localhost:5000"
)

# how many rows to display in tables
CONST_MAX_RECORDS = 50000

CONST_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

DEFAULT_USER_EMAIL = "default_user@localhost"
DEFAULT_USER_PASS = (
    os.environ["DT_DEFAULT_USER_PASS"] if "DT_DEFAULT_USER_PASS" in os.environ else None
)

# The following are some examples of how one might store URLs and API keys
# for data sources that we want to use for data ingress.

# Weather-related misc constants
CONST_LAT = os.environ["DT_LAT"] if "DT_LAT" in os.environ else "DUMMY"  #  latitude
CONST_LON = os.environ["DT_LONG"] if "DT_LONG" in os.environ else "DUMMY"  #  longitude

# We use OpenWeatherMap as an example of how to get weather data
# (both historical and forecast).

CONST_OPENWEATHERMAP_APIKEY = (
    os.environ["DT_OPENWEATHERMAP_APIKEY"].strip()
    if "DT_OPENWEATHERMAP_APIKEY" in os.environ
    else "DUMMY"
)

# see https://openweathermap.org/api/one-call-3
CONST_OPENWEATHERMAP_HISTORICAL_URL = (
    "https://api.openweathermap.org/data/2.5/onecall/timemachine?"
    f"lat={CONST_LAT}&lon={CONST_LON}&units=metric&appid={CONST_OPENWEATHERMAP_APIKEY}"
)  # historical weather URL without requested timestamp
CONST_OPENWEATHERMAP_FORECAST_URL = (
    f"https://api.openweathermap.org/data/3.0/onecall?"
    f"lat={CONST_LAT}&lon={CONST_LON}&units=metric&appid={CONST_OPENWEATHERMAP_APIKEY}"
)

JWT_ACCESS_TOKEN_EXPIRES = int(
    os.environ.get("DT_JWT_ACCESS_TOKEN_EXPIRES_SECONDS", 3600)
)
JWT_REFRESH_TOKEN_EXPIRES = JWT_ACCESS_TOKEN_EXPIRES + 3600
