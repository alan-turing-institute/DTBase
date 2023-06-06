"""
Utility functions for e.g. uploading ingressed data to the db.
"""
import os
import json
import logging
import requests
from dtbase.core.constants import (
    CONST_BACKEND_URL,
)


def backend_call(request_type, end_point_path, payload):
    request_func = getattr(requests, request_type)
    url = f"{CONST_BACKEND_URL}{end_point_path}"
    headers = {"content-type": "application/json"}
    response = request_func(url, headers=headers, json=payload)
    return response


def log_rest_response(response):
    msg = f"Got response {response.status_code}: {response.text}"
    if 300 > response.status_code:
        logging.info(msg)
    else:
        logging.warning(msg)


def add_sensor_types(sensor_types):
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
    """
    for sensor_type in sensor_types:
        logging.info(f"Inserting sensor type {sensor_type['name']}")
        response = backend_call("post", "/sensor/insert_sensor_type", sensor_type)
        log_rest_response(response)


def add_sensors(sensors):
    """
    Add sensors to the database.
    Args:
        sensors: dict of format {<sensor_uniq_id:str>: {"type":<sensor_type:str>, ...}, ...}

    """
    for sensor_id, sensor_info in sensors.items():
        sensor_type = sensor_info["type"]
        logging.info(f"Inserting sensor {sensor_id}")
        payload = {}  # sensor_info
        payload["unique_identifier"] = sensor_id

        response = backend_call("post", f"/sensor/insert_sensor/{sensor_type}", payload)
        log_rest_response(response)
