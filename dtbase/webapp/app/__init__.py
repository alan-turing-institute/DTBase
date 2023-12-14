import datetime as dt
from importlib import import_module
from logging import DEBUG, StreamHandler, basicConfig, getLogger
from os import path
from typing import Any, Union

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    session,
    url_for,
)
from flask_cors import CORS
from flask_login import LoginManager, login_user
from requests.exceptions import ConnectionError
from werkzeug.wrappers import Response

from dtbase.core.constants import DEFAULT_USER_EMAIL, DEFAULT_USER_PASS
from dtbase.webapp.config import AutoLoginConfig, Config
from dtbase.webapp.exc import AuthorizationError
from dtbase.webapp.user import User

login_manager = LoginManager()


@login_manager.user_loader
def load_user(email: str) -> User:
    return User.get(email)


def register_extensions(app: Flask) -> None:
    login_manager.init_app(app)


def register_blueprints(app: Flask) -> None:
    module_list = ("base", "home", "sensors", "locations", "models", "users")

    for module_name in module_list:
        module = import_module("dtbase.webapp.app.{}.routes".format(module_name))
        print(f"Registering blueprint for {module_name}")
        app.register_blueprint(module.blueprint)


def register_template_filters(app: Flask) -> None:
    @app.template_filter()
    def format_datetime(value: dt.datetime) -> Union[dt.datetime, str]:
        try:
            return value.strftime("%Y-%m-%d %H:%M")
        except (ValueError, AttributeError):
            return value


def configure_logs(app: Flask) -> None:
    basicConfig(filename="error.log", level=DEBUG)
    logger = getLogger()
    logger.addHandler(StreamHandler())


def apply_themes(app: Flask) -> None:
    """
    Add support for themes.

    If DEFAULT_THEME is set then all calls to
      url_for('static', filename='')
      will modfify the url to include the theme name

    The theme parameter can be set directly in url_for as well:
      ex. url_for('static', filename='', theme='')

    If the file cannot be found in the /static/<theme>/ lcation then
      the url will not be modified and the file is expected to be
      in the default /static/ location
    """

    @app.context_processor
    def override_url_for() -> dict:
        return dict(url_for=_generate_url_for_theme)

    def _generate_url_for_theme(endpoint: str, **values: Any) -> str:
        if endpoint.endswith("static"):
            themename = values.get("theme", None) or app.config.get(
                "DEFAULT_THEME", None
            )
            if themename:
                theme_file = "{}/{}".format(themename, values.get("filename", ""))
                if path.isfile(path.join(app.static_folder, theme_file)):
                    values["filename"] = theme_file
        return url_for(endpoint, **values)


def register_error_handlers(app: Flask) -> None:
    @login_manager.unauthorized_handler
    def unauthorized_callback() -> Response:
        return redirect(url_for("base_blueprint.login"))

    @app.errorhandler(403)
    def access_forbidden(error: Any) -> Response:
        return redirect(url_for("base_blueprint.login"))

    @app.errorhandler(404)
    def not_found_error(error: Any) -> tuple[str, int]:
        return render_template("errors/page_404.html"), 404

    @app.errorhandler(500)
    def internal_error(error: Any) -> tuple[str, int]:
        return render_template("errors/page_500.html"), 500

    @app.errorhandler(AuthorizationError)
    def authorization_error(_: AuthorizationError) -> Response:
        flash("Unable to authorize the user. Please try loging in again.", "error")
        return redirect(url_for("base_blueprint.login"))

    @app.errorhandler(ConnectionError)
    def connection_error(_: ConnectionError) -> Response:
        flash("Unable to authorize the user. Please try loging in again.", "error")
        return redirect(url_for("base_blueprint.route_backend_not_found"))


def set_autologin(app: Flask) -> None:
    """Make every Flask session log in as the default user."""

    @app.before_request
    def autologin() -> None:
        if "init" not in session:
            user = User(DEFAULT_USER_EMAIL)
            try:
                assert DEFAULT_USER_PASS is not None
                user.authenticate(DEFAULT_USER_PASS)
                login_user(user)
            except (AuthorizationError, AssertionError):
                app.logger.warning("Logging in as default user failed")


def create_app(config: Config) -> Flask:
    if not config.SECRET_KEY:
        raise RuntimeError("Environment variable DT_FRONT_SECRET_KEY must be set.")
    app = Flask(__name__, static_folder="base/static")
    app.config.from_object(config)
    register_extensions(app)
    register_blueprints(app)
    register_template_filters(app)
    register_error_handlers(app)
    configure_logs(app)
    apply_themes(app)
    CORS(app)
    if config == AutoLoginConfig:
        set_autologin(app)
    return app
