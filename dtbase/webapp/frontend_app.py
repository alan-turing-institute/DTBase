from sys import exit
import os

from dtbase.webapp.config import config_dict
from dtbase.webapp.app import create_app

get_config_mode = os.environ.get("CROP_CONFIG_MODE", "Production")

try:
    config_mode = config_dict[get_config_mode.capitalize()]
except KeyError:
    exit("Error: Invalid CROP_CONFIG_MODE environment variable entry.")

app = create_app(config_mode)
