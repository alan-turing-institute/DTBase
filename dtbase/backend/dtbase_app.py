from os import environ
from sys import exit

from flask_migrate import Migrate
from dtbase.backend.config import config_dict
from dtbase.backend.api import create_app, db

get_config_mode = environ.get("DTBASE_CONFIG_MODE", "Production")

try:
    config_mode = config_dict[get_config_mode.capitalize()]
except KeyError:
    exit("Error: Invalid DTBASE_CONFIG_MODE environment variable entry.")

app = create_app(config_mode)
Migrate(app, db)
