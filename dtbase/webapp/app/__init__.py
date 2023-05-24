from flask import Flask, url_for
from flask_login import LoginManager, login_required, UserMixin
from flask_cors import CORS

from importlib import import_module
from logging import basicConfig, DEBUG, getLogger, StreamHandler
from os import path


login_manager = LoginManager()

# TODO Currently this dummy user makes all login_required requests pass authentication.
# Implement proper user management.
DUMMY_USER = UserMixin()
DUMMY_USER.id = "dummy user"


@login_manager.user_loader
def user_loader(id):
    return DUMMY_USER


@login_manager.request_loader
def request_loader(request):
    return DUMMY_USER


def register_extensions(app):
    login_manager.init_app(app)


def register_blueprints(app):
    module_list = ("base", "home", "locations", "models") # "sensors",

    for module_name in module_list:
        module = import_module("app.{}.routes".format(module_name))
        print(f"Registering blueprint for {module_name}")
        app.register_blueprint(module.blueprint)


def register_template_filters(app):
    @app.template_filter()
    def format_datetime(value):
        try:
            return value.strftime("%Y-%m-%d %H:%M")
        except (ValueError, AttributeError):
            return value


def configure_logs(app):
    basicConfig(filename="error.log", level=DEBUG)
    logger = getLogger()
    logger.addHandler(StreamHandler())


def apply_themes(app):
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
    def override_url_for():
        return dict(url_for=_generate_url_for_theme)

    def _generate_url_for_theme(endpoint, **values):
        if endpoint.endswith("static"):
            themename = values.get("theme", None) or app.config.get(
                "DEFAULT_THEME", None
            )
            if themename:
                theme_file = "{}/{}".format(themename, values.get("filename", ""))
                if path.isfile(path.join(app.static_folder, theme_file)):
                    values["filename"] = theme_file
        return url_for(endpoint, **values)


def create_app(config, selenium=False):
    app = Flask(__name__, static_folder="base/static")
    app.config.from_object(config)

    if selenium:
        app.config["LOGIN_DISABLED"] = True
    register_extensions(app)
    register_blueprints(app)
    register_template_filters(app)
    configure_logs(app)
    apply_themes(app)
    CORS(app)
    return app
