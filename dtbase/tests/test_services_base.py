import pytest

from dtbase.core.constants import DEFAULT_USER_EMAIL, DEFAULT_USER_PASS
from dtbase.services.base import BaseIngress
from dtbase.tests.conftest import AuthenticatedClient

TEST_SENSOR_TYPE = {
    "name": "random type",
    "description": "Random type for testing purposes.",
    "measures": [
        {
            "name": "Measure 1",
            "units": "Unit 1",
            "datatype": "float",
        },
        {"name": "Measure 2", "units": "Unit 2", "datatype": "float"},
    ],
}


TEST_SENSOR = {
    "unique_identifier": "737GBNVUE82HF",
    "type_name": "random type",
    "name": "random name",
    "notes": "This is a random sensor",
}


SENSOR_READINGS = {
    "measure_name": "Measure 1",
    "unique_identifier": "737GBNVUE82HF",
    "readings": [5.0, 1.6, 34.245],
    "timestamps": ["2021-01-01T00:00:00", "2021-01-01T00:00:01", "2021-01-01T00:00:02"],
}


class ExampleIngress(BaseIngress):
    def get_service_data(self) -> list:
        return [
            ("/sensor/insert-sensor-type", TEST_SENSOR_TYPE),
            ("/sensor/insert-sensor", TEST_SENSOR),
            ("/sensor/insert-sensor-readings", SENSOR_READINGS),
        ]


exampleingress = ExampleIngress()


def test_ingress_default_get_service_data() -> None:
    baseingress = BaseIngress()
    with pytest.raises(NotImplementedError):
        baseingress.get_service_data()


def test_ingress_get_service_data() -> None:
    assert exampleingress.get_service_data() == [
        ("/sensor/insert-sensor-type", TEST_SENSOR_TYPE),
        ("/sensor/insert-sensor", TEST_SENSOR),
        ("/sensor/insert-sensor-readings", SENSOR_READINGS),
    ]


def test_ingress_backend_login(conn_backend: AuthenticatedClient) -> None:
    exampleingress._backend_login(DEFAULT_USER_EMAIL, DEFAULT_USER_PASS)
    assert exampleingress.access_token is not None


def test_ingress_post_service_data(conn_backend: AuthenticatedClient) -> None:
    responses = exampleingress.post_service_data(
        [
            ("/sensor/insert-sensor-type", TEST_SENSOR_TYPE),
            ("/sensor/insert-sensor", TEST_SENSOR),
            ("/sensor/insert-sensor-readings", SENSOR_READINGS),
        ]
    )
    for response in responses:
        assert response.status_code < 300
    assert len(responses) == 3


def test_ingress_call__(conn_backend: AuthenticatedClient) -> None:
    responses = exampleingress()
    for response in responses:
        assert response.status_code < 300
    assert len(responses) == 3
