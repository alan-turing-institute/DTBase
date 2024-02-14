from logging import DEBUG, StreamHandler, basicConfig, getLogger

from fastapi import FastAPI
from sqlalchemy.exc import SQLAlchemyError

from dtbase.backend.api.auth.routes import router as auth_router
from dtbase.backend.api.location.routes import router as location_router
from dtbase.backend.api.model.routes import router as model_router
from dtbase.backend.api.sensor.routes import router as sensor_router
from dtbase.backend.api.user.routes import router as user_router
from dtbase.backend.db import (
    create_global_database_connection,
    global_engine,
    global_session_maker,
)
from dtbase.core.constants import (
    DEFAULT_USER_EMAIL,
    DEFAULT_USER_PASS,
    SQL_CONNECTION_STRING,
    SQL_DBNAME,
)
from dtbase.core.structure import Base
from dtbase.core.users import change_password, delete_user, insert_user


def add_routers(app: FastAPI) -> None:
    app.include_router(auth_router)
    app.include_router(location_router)
    app.include_router(model_router)
    app.include_router(user_router)
    app.include_router(sensor_router)


def configure_database(app: FastAPI) -> None:
    create_global_database_connection(SQL_CONNECTION_STRING, SQL_DBNAME)
    engine = global_engine()
    Base.metadata.create_all(bind=engine)


def configure_logs() -> None:
    basicConfig(filename="error.log", level=DEBUG)
    logger = getLogger()
    logger.addHandler(StreamHandler())


def add_default_user(app: FastAPI) -> None:
    """Ensure that there's a default user, with the right credentials."""
    user_info = {
        "email": DEFAULT_USER_EMAIL,
        "password": DEFAULT_USER_PASS,
    }
    session_maker = global_session_maker()
    with session_maker() as session:
        if DEFAULT_USER_PASS is None:
            try:
                delete_user(user_info["email"], session=session)
            except SQLAlchemyError:
                # If the user doesn't exist then nothing to do.
                session.rollback()
        else:
            try:
                insert_user(**user_info, session=session)
            except SQLAlchemyError:
                # Presumably the user exists already, so change their password.
                session.rollback()
                change_password(**user_info, session=session)
            session.commit()


def create_app() -> FastAPI:
    app = FastAPI()
    configure_database(app)
    configure_logs()
    add_default_user(app)
    add_routers(app)
    return app
