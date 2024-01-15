"""
Utility functions for ingressing data to the db.
"""
from typing import Any, List, Optional

from requests import Response

from dtbase.core.constants import (
    DEFAULT_USER_EMAIL,
    DEFAULT_USER_PASS,
)
from dtbase.core.utils import auth_backend_call, log_rest_response, login


class BaseIngress:
    """
    Class to be inherited for specific Ingress examples.
    Provides boilerplate for interacting with the backend.
    TODO: Potentially Include boilerplate for Azure Functions
    """

    def __init__(self) -> None:
        self.access_token = None

    def get_data(self) -> Any:
        """
        Method for getting data from source and returning Backend API Endpoints names
        and payload pairs. This method should be implemented when inheriting from this
        class. The implementation in BaseIngress only raises a NotImplementedError.

        The method should return a list of tuples. A tuple should
        be in the format [(<endpoint_name>, <payload>)]. It must be a list even if
        its a single tuple.

        Below is an example return value for inserting a sensor type and a sensor.
        Please look at backend readme for list of backend endpoints
        and their respective payload formats.

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
                        {
                            "name": "relative humidity",
                            "units": "percent",
                            "datatype": "float"
                        },
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
        raise NotImplementedError(
            "The user should implement this method"
            " by inhering from the BaseIngress class"
            " and overwriting the get_data method."
        )

    def backend_login(self, username: str, password: Optional[str]) -> None:
        """
        Sets the access token using login credentials.

        Raises BackendCallError if the login fails.
        """
        self.access_token = login(username, password)[0]

    def ingress_data(self, *args: Any, **kwargs: Any) -> List[Response]:
        """
        Get data from API and upload to the database via the backend.
        Takes any argument available to the get_data method.

        Args: *args, **kwargs: arguments to be passed to get_data method

        """
        ingress_pairs = self.get_data(*args, **kwargs)
        self.backend_login(DEFAULT_USER_EMAIL, DEFAULT_USER_PASS)

        responses = []
        for ingress_pair in ingress_pairs:
            endpoint, payload = ingress_pair
            response = auth_backend_call(
                "post", endpoint, payload=payload, token=self.access_token
            )
            log_rest_response(response)
            responses.append(response)
        return responses
