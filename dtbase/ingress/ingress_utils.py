"""
Utility functions for e.g. uploading ingressed data to the db.
"""
import logging
from typing import Any, Dict, List, Optional

import requests
from flask import Response

from dtbase.core.constants import CONST_BACKEND_URL


def backend_call(
    request_type: str,
    end_point_path: str,
    payload: Dict[str, Any],
    access_token: Optional[str] = None,
) -> Response:
    """Call the given DTBase backend endpoint, return the response."""
    request_func = getattr(requests, request_type)
    url = f"{CONST_BACKEND_URL}{end_point_path}"
    headers = {"content-type": "application/json"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    response = request_func(url, headers=headers, json=payload)
    return response


def log_rest_response(response: Response) -> None:
    msg = f"Got response {response.status_code}: {response.text}"
    if 300 > response.status_code:
        logging.info(msg)
    else:
        logging.warning(msg)


def backend_login(username: str, password: str) -> str:
    response = backend_call(
        "post", "/auth/login", payload={"email": username, "password": password}
    )
    if response.status_code != 200:
        raise RuntimeError(f"Failed to authenticate with the backend: {response}")
    assert response.json is not None
    return response.json()["access_token"]


def add_sensor_types(sensor_types: List[dict], access_token: str) -> None:
    """
    Add sensor types to the database
    Args:
        sensor_types: list of dicts, format:
            [
             { "name": <sensor_type_name:str>,
               "description": <description:str>,
               "measures": [
                            { "name": <measure_name:str>,
                              "units": <measure_units:str>,
                              "datatype": <"float"|"integer"|"string"|"boolean">
                            }, ...
                           ],
             }, ...
           ]
        access_token: str, access token for the backend
    """
    for sensor_type in sensor_types:
        logging.info(f"Inserting sensor type {sensor_type['name']}")
        response = backend_call(
            "post", "/sensor/insert-sensor-type", sensor_type, access_token=access_token
        )
        log_rest_response(response)


def add_sensors(sensors: List[dict], access_token: str) -> None:
    """
    Add sensors to the database.
    Args:
        sensors: list of dicts, of format:
           [
            { "unique_identifier": <sensor_uniq_id:str>,
              "type_name":<sensor_type:str>
            }, ...
           ]
        access_token: str, access token for the backend
    """
    for sensor_info in sensors:
        logging.info(f"Inserting sensor {sensor_info['unique_identifier']}")
        payload = sensor_info
        response = backend_call(
            "post", "/sensor/insert-sensor", payload, access_token=access_token
        )
        log_rest_response(response)
