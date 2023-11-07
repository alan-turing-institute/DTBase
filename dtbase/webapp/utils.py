"""Utilities for the front end."""
import datetime as dt
import urllib
from typing import Any, Dict, List, Optional

import requests
from flask import Response

from dtbase.core.constants import CONST_BACKEND_URL as BACKEND_URL


def parse_rfc1123_datetime(string: str) -> dt.datetime:
    """Parse an RFC 1123 formatted datetime string into a datetime object.

    The backend returns this format, it's a web standard.
    """
    return dt.datetime.strptime(string, "%a, %d %b %Y %H:%M:%S GMT")


def parse_url_parameter(request, parameter: str) -> Optional[str, None]:
    """Parse a URL parameter, doing any unquoting as necessary. Return None if the
    parameter doesn't exist.
    """
    raw = request.args.get(parameter)
    if raw is not None:
        parsed = urllib.parse.unquote(raw)
    else:
        parsed = None
    return parsed


def backend_call(
    request_type: str, end_point_path: str, payload: Optional[dict] = None
) -> Response:
    """Make an API call to the backend server."""
    request_func = getattr(requests, request_type)
    url = f"{BACKEND_URL}{end_point_path}"
    if payload:
        headers = {"content-type": "application/json"}
        response = request_func(url, headers=headers, json=payload)
    else:
        response = request_func(url)
    return response


def convert_form_values(
    variables: List[Dict[str, Any]], form: dict, prefix: str = "identifier"
) -> Dict[str, Any]:
    """
    Prepared the form and converts values to their respective datatypes as defined in
    the schema. Returns a dictionary of converted values.
    """

    # Define a dictionary mapping type names to conversion functions
    conversion_functions = {
        "integer": int,
        "float": float,
        "string": str,
        "boolean": lambda x: x.lower() == "true",
    }

    converted_values = {}

    for variable in variables:
        value = form.get(f"{prefix}_{variable['name']}")
        datatype = variable["datatype"]

        # Get the conversion function for this datatype
        conversion_function = conversion_functions.get(datatype)

        if not conversion_function:
            raise ValueError(
                f"Unknown datatype '{datatype}' for variable '{variable['name']}'"
            )

        try:
            # Convert the value to the correct datatype
            converted_value = conversion_function(value)
        except ValueError:
            raise ValueError(
                f"Invalid value '{value}' for variable '{variable['name']}' "
                f"(expected {datatype})"
            )

        converted_values[variable["name"]] = converted_value

    return converted_values
