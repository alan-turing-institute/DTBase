from importlib import import_module
from logging import DEBUG, StreamHandler, basicConfig, getLogger
from typing import Optional

import flask_jwt_extended as fjwt
from flask import Flask
from flask_cors import CORS
from sqlalchemy.exc import SQLAlchemyError

from dtbase.backend.config import Config
from dtbase.core.constants import (
    DEFAULT_USER_EMAIL,
    DEFAULT_USER_PASS,
    JWT_ACCESS_TOKEN_EXPIRES,
    JWT_REFRESH_TOKEN_EXPIRES,
)
from dtbase.core.structure import SQLA as db
from dtbase.core.users import change_password, delete_user, insert_user


def register_extensions(app: Flask) -> None:
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = JWT_ACCESS_TOKEN_EXPIRES
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = JWT_REFRESH_TOKEN_EXPIRES
    fjwt.JWTManager(app)
    db.init_app(app)


def register_blueprints(app: Flask) -> None:
    module_list = ("auth", "location", "sensor", "model", "user")

    for module_name in module_list:
        module = import_module("dtbase.backend.api.{}.routes".format(module_name))
        app.register_blueprint(module.blueprint)


def configure_database(app: Flask) -> None:
    with app.app_context():
        db.create_all()

    @app.teardown_request
    def shutdown_session(exception: Optional[Exception] = None) -> None:
        db.session.remove()


def configure_logs(app: Flask) -> None:
    basicConfig(filename="error.log", level=DEBUG)
    logger = getLogger()
    logger.addHandler(StreamHandler())


def add_default_user(app: Flask) -> None:
    """Ensure that there's a default user, with the right credentials."""
    with app.app_context():
        user_info = {
            "email": DEFAULT_USER_EMAIL,
            "password": DEFAULT_USER_PASS,
        }
        session = db.session
        session.begin()
        if DEFAULT_USER_PASS is None:
            try:
                delete_user(**user_info, session=session)
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


def create_app(config: Config) -> Flask:
    if not config.SECRET_KEY:
        raise RuntimeError("The environment variable DT_JWT_SECRET_KEY must be set.")
    app = Flask(__name__)
    app.config.from_object(config)
    register_extensions(app)
    register_blueprints(app)
    configure_database(app)
    configure_logs(app)
    CORS(app)
    add_default_user(app)
    return app
