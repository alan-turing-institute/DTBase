"""
Useful database-related functions for predictive models
"""

import logging
from typing import List, Optional

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


def print_rows_head(rows: List[str], numrows: int = 0) -> None:
    logging.info("Printing:{0} of {1}".format(numrows, len(rows)))
    if numrows == 0:
        for row in rows[: len(rows)]:
            logging.info(row)
    else:
        for row in rows[:numrows]:
            logging.info(row)
