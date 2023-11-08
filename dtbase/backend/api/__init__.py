from importlib import import_module
from logging import DEBUG, StreamHandler, basicConfig, getLogger
from typing import Union

from flask import Flask, Request
from flask_cors import CORS
from flask_login import LoginManager, UserMixin

from dtbase.core.constants import (
    DEFAULT_USER_EMAIL,
    DEFAULT_USER_PASS,
    DEFAULT_USER_USERNAME,
)
from dtbase.core.structure import SQLA as db
from dtbase.core.structure import User
from dtbase.core.utils import change_user_password, create_user, delete_user

login_manager = LoginManager()


@login_manager.user_loader
def user_loader(id: int) -> Union[UserMixin, None]:
    return User.query.filter_by(id=id).first()


@login_manager.request_loader
def request_loader(request: Request) -> Union[UserMixin, None]:
    username = request.form.get("username")
    user = User.query.filter_by(username=username).first()
    return user if user else None


def register_extensions(app: Flask) -> None:
    db.init_app(app)
    login_manager.init_app(app)


def register_blueprints(app: Flask) -> None:
    module_list = ("location", "sensor", "model")

    for module_name in module_list:
        module = import_module("dtbase.backend.api.{}.routes".format(module_name))
        app.register_blueprint(module.blueprint)


def configure_database(app: Flask) -> None:
    @app.before_first_request
    def initialize_database() -> None:
        db.create_all()

    @app.teardown_request
    def shutdown_session(exception=None) -> None:
        db.session.remove()


def configure_logs(app: Flask) -> None:
    basicConfig(filename="error.log", level=DEBUG)
    logger = getLogger()
    logger.addHandler(StreamHandler())


def add_default_user(app: Flask) -> None:
    """Ensure that there's a default user, with the right credentials."""
    with app.app_context():
        if DEFAULT_USER_PASS is None:
            delete_user(username=DEFAULT_USER_USERNAME, email=DEFAULT_USER_EMAIL)
        else:
            user_info = {
                "username": DEFAULT_USER_USERNAME,
                "email": DEFAULT_USER_EMAIL,
                "password": DEFAULT_USER_PASS,
            }
            success, _ = create_user(**user_info)
            if not success:
                # Presumably the user exists already, so change their password.
                change_user_password(**user_info)


def create_app(config: Union[object, str]) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config)
    register_extensions(app)
    register_blueprints(app)
    configure_database(app)
    configure_logs(app)
    CORS(app)
    add_default_user(app)
    return app
