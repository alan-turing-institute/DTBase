"""
Python module to read the parameters specified in the configuration file.
"""

import ast
import os
from configparser import ConfigParser
from typing import Any


def read_config(
    # gets config.ini file from the parent directory, no matter where the script is run
    # from
    section: str,
    filename: str = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "dataprocessor/data_config.ini"
    ),
) -> dict[str, Any]:
    # check that configuration file exists
    if not os.path.isfile(filename):
        raise Exception(f"File {filename} does not exist")

    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename, encoding="utf-8-sig")

    # get section and save as a dictionary
    conf_dict = {}
    if parser.has_section(section):
        params = parser.items(section)  # returns a list with item name and item value
        for param in params:
            try:
                # use ast.literal_eval to convert a string to a Python literal structure
                conf_dict[param[0]] = ast.literal_eval(parser.get(section, param[0]))
            except Exception as e:
                print(f"Error while parsing '{param[0]}': {e}")
                raise
    else:
        raise Exception(
            "Section {0} not found in the {1} file".format(section, filename)
        )

    # If the same variable is defined also as an environment variable, have that
    # override the value in the file.
    # Note that the environment variable must follow this structure:
    # DT_ARIMA_VARIABLENAME
    for key in conf_dict.keys():
        env_var = "DT_ARIMA_{}".format(key).upper()
        if env_var in os.environ:
            # use ast.literal_eval to convert a string to a Python literal structure
            conf_dict[key] = ast.literal_eval(os.environ[env_var])
    return conf_dict
