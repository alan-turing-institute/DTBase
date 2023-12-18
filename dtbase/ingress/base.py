"""
Utility functions for e.g. uploading ingressed data to the db.
"""
import logging
from typing import Any, Dict, List

import requests
from flask import Response

from dtbase.core.constants import (
    CONST_BACKEND_URL,
    DEFAULT_USER_EMAIL,
    DEFAULT_USER_PASS,
)


class BaseIngress:
    """
    Class to be inherited for specific Ingress examples.
    Provides boilerplate for interacting with the backend.
    TODO: Potentially Include boilerplate for Azure Functions
    """

    def __init__(self) -> None:
        self.access_token = None

    def get_data() -> NotImplementedError:
        """
        Method for getting data from source and returning Backend API Endpoints names
        and payload pairs. This method should be implemented when inheriting from this
        class.
        The method should return a list of tuples. A tuple should
        be in the format [(<endpoint_name>, <payload>)]. It must be a list even if
        its a single tuple.

        Below is an example for inserting a sensor type and a sensor.
        Please look at backend readme for list of backend endpoints
        and their repsective payload formats.

        [
            (
                "/sensor/insert-sensor-type",
                {
                    "name": "Weather",
                    "description": (
                        "Weather sensors and sensor-like data sources, "
                        "such as weather forecast sources."
                    ),
                    "measures": [
                        {
                            "name": "temperature",
                            "units": "degrees Celsius",
                            "datatype": "float",
                        },
                        {"name": "relative humidity", "units": "percent",
                        "datatype": "float"},
                    ],
                },
            ),
            (
                "/sensor/insert-sensor",
                {
                    "unique_identifier": "OpenWeatherMapHistory",
                    "type_name": "Weather",
                    "name": "OpenWeatherMap Historical Data",
                },
            ),
        ]

        """
        raise NotImplementedError()

    def backend_login(self, username: str, password: str) -> None:
        """
        Sets the access token using login credentials
        """
        response = self.backend_call(
            "post", "/auth/login", payload={"email": username, "password": password}
        )
        if response.status_code != 200:
            raise RuntimeError(f"Failed to authenticate with the backend: {response}")
        assert response.json is not None
        self.access_token = response.json()["access_token"]

    def backend_call(
        self,
        request_type: str,
        end_point_path: str,
        payload: Dict[str, Any],
    ) -> Response:
        """Call the given DTBase backend endpoint, return the response."""
        request_func = getattr(requests, request_type)
        url = f"{CONST_BACKEND_URL}{end_point_path}"
        headers = {"content-type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        response = request_func(url, headers=headers, json=payload)
        return response

    def log_rest_response(self, response: Response) -> None:
        msg = f"Got response {response.status_code}: {response.text}"
        if 300 > response.status_code:
            logging.info(msg)
        else:
            logging.warning(msg)

    def add_sensor_types(self, sensor_types: List[dict]) -> None:
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
            response = self.backend_call(
                "post",
                "/sensor/insert-sensor-type",
                sensor_type,
                access_token=self.access_token,
            )
            self.log_rest_response(response)

    def add_sensors(self, sensors: List[dict]) -> None:
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
            response = self.backend_call(
                "post", "/sensor/insert-sensor", payload, access_token=self.access_token
            )
            self.log_rest_response(response)

    def ingress_data(self, *args: Any, **kwargs: Any) -> None:
        """
        Get data from API and upload to the database via the backend.
        Takes any argument available to the get_data method.

        """
        api_responses = self.get_data(*args, **kwargs)
        self.backend_login(DEFAULT_USER_EMAIL, DEFAULT_USER_PASS)
        for api_response in api_responses:
            endpoint, payload = api_response
            backend_response = self.backend_call("post", endpoint, payload)
            self.log_rest_response(backend_response)
