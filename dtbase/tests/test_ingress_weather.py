from datetime import datetime, timedelta

import pytest
import requests_mock
from freezegun import freeze_time

from dtbase.ingress.ingress_weather import (
    SENSOR_OPENWEATHERMAPFORECAST,
    SENSOR_OPENWEATHERMAPHISTORICAL,
    OpenWeatherDataIngress,
)
from dtbase.tests.conftest import AuthenticatedClient
from dtbase.tests.resources.data_for_tests import (
    EXPECTED_OPENWEATHERMAP_FORECAST_GET_DATA_RESPONSE,
    EXPECTED_OPENWEATHERMAP_HISTORICAL_GET_DATA_RESPONSE,
    MOCKED_CONST_OPENWEATHERMAP_FORECAST_URL_RESPONSE,
    MOCKED_CONST_OPENWEATHERMAP_HISTORICAL_URL_RESPONSE,
)

NOW = datetime.now()
open_weather_data_ingress = OpenWeatherDataIngress()

FORECAST_BASE_URL = "https://api.openweathermap.org/data/3.0/onecall"
HISTORICAL_BASE_URL = "https://api.openweathermap.org/data/2.5/onecall/timemachine"
API_KEY = "api_key"
LATITUDE = 0
LONGITUDE = 1


@pytest.mark.parametrize(
    "dt_from, dt_to, expected",
    [
        (
            NOW - timedelta(hours=72),
            "present",
            (
                (
                    HISTORICAL_BASE_URL
                    + f"?lat={LATITUDE}&lon={LONGITUDE}&units=metric&appid={API_KEY}"
                ),
                SENSOR_OPENWEATHERMAPHISTORICAL,
                NOW - timedelta(hours=72),
                open_weather_data_ingress.present,
            ),
        ),
        (
            "present",
            NOW + timedelta(days=1),
            (
                (
                    FORECAST_BASE_URL
                    + f"?lat={LATITUDE}&lon={LONGITUDE}&units=metric&appid={API_KEY}"
                ),
                SENSOR_OPENWEATHERMAPFORECAST,
                open_weather_data_ingress.present,
                NOW + timedelta(days=1),
            ),
        ),
    ],
)
def test_get_api_base_url_and_sensor(
    dt_from: datetime,
    dt_to: datetime,
    expected: tuple[str, dict[str, str], datetime, datetime],
) -> None:
    """Test the get_api_base_url_and_sensor method for scenarios where the correct //
    API base URL and sensor should be returned"""
    assert (
        open_weather_data_ingress.get_api_base_url_and_sensor(
            dt_from, dt_to, API_KEY, LATITUDE, LONGITUDE
        )
        == expected
    )


@pytest.mark.parametrize(
    "dt_from, dt_to, expected",
    [
        (NOW - timedelta(days=21), "present", ValueError),
        ("present", NOW + timedelta(days=12), ValueError),
        ("present", "present", ValueError),
        (NOW + timedelta(days=2), "present", ValueError),
        (NOW - timedelta(days=2), NOW + timedelta(days=2), ValueError),
    ],
)
def test_get_api_base_url_and_sensor_raises(
    dt_from: datetime, dt_to: datetime, expected: ValueError
) -> None:
    """Test the get_api_base_url_and_sensor method for scenarios where an error //
    should be raised"""
    with pytest.raises(expected):
        open_weather_data_ingress.get_api_base_url_and_sensor(
            dt_from, dt_to, API_KEY, LATITUDE, LONGITUDE
        )


@freeze_time("2024-01-06")
def test_get_data_historical_api(conn_backend: AuthenticatedClient) -> None:
    """Test the get_data method for a scenario where the historical API would be used"""
    weather_ingress = OpenWeatherDataIngress()
    dt_to = datetime(2024, 1, 5, 16, 1, 1, 1)
    dt_from = dt_to - timedelta(hours=2)
    with requests_mock.Mocker() as m:
        m.get(
            HISTORICAL_BASE_URL,
            json=MOCKED_CONST_OPENWEATHERMAP_HISTORICAL_URL_RESPONSE,
        )
        response = weather_ingress.get_service_data(
            dt_from, dt_to, API_KEY, LATITUDE, LONGITUDE
        )
        assert response == EXPECTED_OPENWEATHERMAP_HISTORICAL_GET_DATA_RESPONSE

        responses = weather_ingress(
            dt_from=dt_from,
            dt_to=dt_to,
            api_key=API_KEY,
            latitude=LATITUDE,
            longitude=LONGITUDE,
        )
        for response in responses:
            assert response.status_code < 300
        assert len(responses) == 9


@freeze_time("2024-01-04")
def test_get_data_forecast_api(conn_backend: AuthenticatedClient) -> None:
    """Test the get_data method for a scenario where the forecast API would be used"""
    weather_ingress = OpenWeatherDataIngress()
    dt_from = datetime(2024, 1, 5, 16, 1, 1, 1)
    dt_to = dt_from + timedelta(hours=2)
    with requests_mock.Mocker() as m:
        m.get(
            FORECAST_BASE_URL,
            json=MOCKED_CONST_OPENWEATHERMAP_FORECAST_URL_RESPONSE,
        )
        response = weather_ingress.get_service_data(
            dt_from, dt_to, API_KEY, LATITUDE, LONGITUDE
        )
        assert response == EXPECTED_OPENWEATHERMAP_FORECAST_GET_DATA_RESPONSE

        responses = weather_ingress(
            dt_from=dt_from,
            dt_to=dt_to,
            api_key=API_KEY,
            latitude=LATITUDE,
            longitude=LONGITUDE,
        )
        for response in responses:
            assert response.status_code < 300
        assert len(responses) == 9
