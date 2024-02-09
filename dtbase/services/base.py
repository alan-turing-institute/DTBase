"""
Base class for all services used in the application.
"""
from typing import Any, List, Optional

from requests import Response

from dtbase.core.constants import (
    DEFAULT_USER_EMAIL,
    DEFAULT_USER_PASS,
)
from dtbase.core.utils import auth_backend_call, log_rest_response, login


class BaseService:
    """
    Base class for all services. Users inherit this class to write custom modelling and
    data ingress services. The user should implement the following methods:
    """

    def __init__(self) -> None:
        self.access_token = None
        self.service_type = None

    def _backend_login(self, username: str, password: Optional[str]) -> None:
        """
        Sets the access token using login credentials.

        Raises BackendCallError if the login fails.
        """
        self.access_token = login(username, password)[0]

    def get_service_data(self) -> None:
        """
        Method for getting data from a source and returning Backend API Endpoints names
        and payload pairs. This method should be implemented when inheriting from this
        class. The implementation in BaseService only raises a NotImplementedError.

        The method should return a list of tuples. A tuple should
        be in the format [(<endpoint_name>, <payload>)]. It must be a list even if
        its a single tuple.

        There is more information in the docstrings of the BaseIngress and BaseModel
        get_service_data methods about the expected format of the tuples.
        """
        raise NotImplementedError(
            "The user should implement this method"
            " by inheriting from the BaseService class"
            " and overwriting the get_service_data method."
        )

    def post_service_data(
        self,
        data_pairs: List[tuple],
        dt_user_email: Optional[str] = None,
        dt_user_password: Optional[str] = None,
    ) -> List[Response]:
        """
        Upload data to the database via the backend via a post request.
        Handles unpacking of data pairs and returns responses from the backend.

        Args:
            data_pairs: list of tuples of the form [(<endpoint_name>, <payload>)].
            It must be a list even if its a single tuple. Typically, this is the output
            from self.run().
            dt_user_email: email of the backend user to login with. By default read from
                the environment variable DT_DEFAULT_USER_EMAIL.
            dt_user_password: password of the backend user to login with. By default
                read from the environment variable DT_DEFAULT_USER_PASS.

        Returns:
            List of responses from the backend API calls.
        """
        if dt_user_email is None:
            dt_user_email = DEFAULT_USER_EMAIL
        if dt_user_password is None:
            dt_user_password = DEFAULT_USER_PASS

        self._backend_login(dt_user_email, dt_user_email)

        responses = []
        for data_pair in data_pairs:
            endpoint, payload = data_pair
            response = auth_backend_call(
                "post", endpoint, payload=payload, token=self.access_token
            )
            log_rest_response(response)
            responses.append(response)
        return responses

    def __call__(
        self,
        dt_user_email: Optional[str] = None,
        dt_user_password: Optional[str] = None,
        **kwargs: Any,
    ) -> List[Response]:
        """
        This method will 'call' or run the service.
        It runs the get_service_data and post_service_data methods in sequence.

        Args and Kwargs are passed to the get_service_data method.
        """
        data_pairs = self.get_service_data(**kwargs)
        return self.post_service_data(data_pairs, dt_user_email, dt_user_password)

    def schedule(self) -> None:
        """
        This method will handle the scheduling of the service.
        Arguments taken in this method will control how often __call__ method is called.
        """
        pass


class BaseIngress(BaseService):
    """
    Class to be inherited for custom data Ingress.
    The user should implement the call method.
    The call method should return a list of tuples. A tuple should
    be in the format [(<endpoint_name>, <payload>)]. It must be a list even if
    its a single tuple.
    """

    def __init__(self) -> None:
        super().__init__()
        self.service_type = "ingress"

    def get_service_data(self) -> None:
        """
        Method for getting data from a source and returning Backend API Endpoints names
        and payload pairs. This method should be implemented when inheriting from this
        class. The implementation in BaseService only raises a NotImplementedError.

        The method should return a list of tuples. A tuple should
        be in the format [(<endpoint_name>, <payload>)]. It must be a list even if
        its a single tuple.

        For an Ingress Service, this would typically look like:
        return [
            ("/sensor/insert-sensor-type", TEST_SENSOR_TYPE),
            ("/sensor/insert-sensor", TEST_SENSOR),
            ("/sensor/insert-sensor-readings", SENSOR_READINGS),
        ]


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
            " by inheriting from the BaseService class"
            " and overwriting the get_service_data method."
        )


class BaseModel(BaseService):
    def __init__(self) -> None:
        super().__init__()
        self.service_type = "model"

    def get_service_data(self) -> None:
        """
        Method for getting data from a source and returning Backend API Endpoints names
        and payload pairs. This method should be implemented when inheriting from this
        class. The implementation in BaseService only raises a NotImplementedError.

        The method should return a list of tuples. A tuple should
        be in the format [(<endpoint_name>, <payload>)]. It must be a list even if
        its a single tuple.

        For a Model Service, this would typically look like:
        return [
            ("/model/insert-model", MODEL_PAYLOAD),
            ("/model/insert-model-parameters", MODEL_PARAMETERS_PAYLOAD),
            ("/model/insert-model-predictions", MODEL_PREDICTIONS_PAYLOAD),
        ]

        Below is an example return value for inserting a model and its parameters.
        """
        raise NotImplementedError(
            "The user should implement this method"
            " by inheriting from the BaseModel class"
            " and overwriting the get_service_data method."
        )
