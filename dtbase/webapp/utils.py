"""Utilities for the front end."""
import datetime as dt
import os
import json
import requests
import urllib

BACKEND_URL = os.environ["DT_BACKEND_URL"]


def parse_rfc1123_datetime(string):
    """Parse an RFC 1123 formatted datetime string into a datetime object.

    The backend returns this format, it's a web standard.
    """
    return dt.datetime.strptime(string, "%a, %d %b %Y %H:%M:%S GMT")


def parse_url_parameter(request, parameter):
    """Parse a URL parameter, doing any unquoting as necessary. Return None if the
    parameter doesn't exist.
    """
    raw = request.args.get(parameter)
    if raw is not None:
        parsed = urllib.parse.unquote(raw)
    else:
        parsed = None
    return parsed


def backend_call(request_type, end_point_path, payload=None):
    """Make an API call to the backend server."""
    request_func = getattr(requests, request_type)
    url = f"{BACKEND_URL}{end_point_path}"
    if payload:
        headers = {"content-type": "application/json"}
        response = request_func(url, headers=headers, json=json.dumps(payload))
    else:
        response = request_func(url)
    return response
