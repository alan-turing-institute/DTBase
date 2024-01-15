"""
Useful database-related functions for predictive models
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from dtbase.core.constants import SQL_CONNECTION_STRING, SQL_DBNAME

# The below import is for exporting, other modules will import it from there
from dtbase.core.db import (
    connect_db,
    session_close,  # noqa: F401
    session_open,
)

logger = logging.getLogger(__name__)


def get_sqlalchemy_session(
    connection_string: Optional[str] = None, dbname: Optional[str] = None
) -> Session:
    """
    For other functions in this module, if no session is provided as an argument,
    they will call this to get a session using default connection string.
    """
    if not connection_string:
        connection_string = SQL_CONNECTION_STRING
    if not dbname:
        dbname = SQL_DBNAME
    engine = connect_db(connection_string, dbname)
    session = session_open(engine)
    return session
