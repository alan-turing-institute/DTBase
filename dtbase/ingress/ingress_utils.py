"""
Utility functions for e.g. uploading ingressed data to the db.
"""
import logging
from typing import List

from flask import Response

from dtbase.core.utils import backend_call


def log_rest_response(response: Response) -> None:
    msg = f"Got response {response.status_code}: {response.text}"
    if 300 > response.status_code:
        logging.info(msg)
    else:
        logging.warning(msg)


def add_sensor_types(sensor_types: List[dict]) -> None:
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
        response = backend_call("post", "/sensor/insert-sensor-type", sensor_type)
        log_rest_response(response)


def add_sensors(sensors: List[dict]) -> None:
    """
    Add sensors to the database.
    Args:
        sensors: list of dicts, of format:
           [
            { "unique_identifier": <sensor_uniq_id:str>,
              "type_name":<sensor_type:str>
            }, ...
           ]
    """
    for sensor_info in sensors:
        logging.info(f"Inserting sensor {sensor_info['unique_identifier']}")
        payload = sensor_info
        response = backend_call("post", "/sensor/insert-sensor", payload)
        log_rest_response(response)
