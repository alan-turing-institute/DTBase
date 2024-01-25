"""
Python module to read the parameters specified in the configuration file.
"""
from __future__ import annotations

import ast
import os
from configparser import ConfigParser
from typing import Any


def read_config(filename: str, section: str) -> dict[str, Any]:
    """Read a section from a .init file and return a dictionary with the parameters.

    Overrides any values from the file with ones read from environment variables, if
    set.
    """
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
    # DT_VARIABLENAME
    for key in conf_dict.keys():
        env_var = "DT_{}".format(key).upper()
        if env_var in os.environ:
            # use ast.literal_eval to convert a string to a Python literal structure
            conf_dict[key] = ast.literal_eval(os.environ[env_var])
    return conf_dict
