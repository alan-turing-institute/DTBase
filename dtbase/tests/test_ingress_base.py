import pytest
from fastapi.testclient import TestClient

from dtbase.core.constants import DEFAULT_USER_EMAIL, DEFAULT_USER_PASS
from dtbase.ingress.ingress_base import BaseIngress

test_ingress = BaseIngress()

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
    def get_data(self) -> list:
        return [
            ("/sensor/insert-sensor-type", TEST_SENSOR_TYPE),
            ("/sensor/insert-sensor", TEST_SENSOR),
            ("/sensor/insert-sensor-readings", SENSOR_READINGS),
        ]


def test_get_data() -> None:
    with pytest.raises(NotImplementedError):
        test_ingress.get_data()


def test_backend_login(conn_backend: TestClient) -> None:
    test_ingress.backend_login(DEFAULT_USER_EMAIL, DEFAULT_USER_PASS)
    assert test_ingress.access_token is not None


def test_ingress_base(conn_backend: TestClient) -> None:
    responses = ExampleIngress().ingress_data()
    for response in responses:
        assert response.status_code < 300
    assert len(responses) == 3
