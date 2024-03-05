from typing import Generator, Optional

from sqlalchemy.engine import Engine
from sqlalchemy.orm.session import sessionmaker

from dtbase.core.db import Session
from dtbase.core.utils import connect_db

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
