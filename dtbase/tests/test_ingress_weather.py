from datetime import datetime, timedelta

import pytest
import requests_mock

from dtbase.core.constants import (
    CONST_OPENWEATHERMAP_FORECAST_URL,
    CONST_OPENWEATHERMAP_HISTORICAL_URL,
)
from dtbase.ingress.ingress_weather import (
    SENSOR_OPENWEATHERMAPFORECAST,
    SENSOR_OPENWEATHERMAPHISTORICAL,
    OpenWeatherDataIngress,
)
from dtbase.tests.resources.data_for_tests import (
    EXPECTED_OPENWEATHERMAP_FORECAST_GET_DATA_RESPONSE,
    EXPECTED_OPENWEATHERMAP_HISTORICAL_GET_DATA_RESPONSE,
    MOCKED_CONST_OPENWEATHERMAP_FORECAST_URL_RESPONSE,
    MOCKED_CONST_OPENWEATHERMAP_HISTORICAL_URL_RESPONSE,
)

NOW = datetime.now()
open_weather_data_ingress = OpenWeatherDataIngress()


@pytest.mark.parametrize(
    "dt_from, dt_to, expected",
    [
        (
            NOW - timedelta(hours=72),
            "present",
            (
                CONST_OPENWEATHERMAP_HISTORICAL_URL,
                SENSOR_OPENWEATHERMAPHISTORICAL,
                NOW - timedelta(hours=72),
                open_weather_data_ingress.present,
            ),
        ),
        (
            "present",
            NOW + timedelta(days=1),
            (
                CONST_OPENWEATHERMAP_FORECAST_URL,
                SENSOR_OPENWEATHERMAPFORECAST,
                open_weather_data_ingress.present,
                NOW + timedelta(days=1),
            ),
        ),
    ],
)
def test_get_api_base_url_and_sensor(
    dt_from: datetime, dt_to: datetime, expected: tuple[str, str]
) -> None:
    """Test the get_api_base_url_and_sensor method for scenarios where the correct //
    API base URL and sensor should be returned"""
    assert (
        open_weather_data_ingress.get_api_base_url_and_sensor(dt_from, dt_to)
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
        open_weather_data_ingress.get_api_base_url_and_sensor(dt_from, dt_to)


def test_get_data_historical_api() -> None:
    """Test the get_data method for a scenario where the historical API would be used"""
    weather_ingress = OpenWeatherDataIngress()
    dt_to = datetime(2024, 1, 5, 16, 1, 1, 1)
    dt_from = dt_to - timedelta(hours=2)
    with requests_mock.Mocker() as m:
        m.get(
            CONST_OPENWEATHERMAP_HISTORICAL_URL,
            json=MOCKED_CONST_OPENWEATHERMAP_HISTORICAL_URL_RESPONSE,
        )
        response = weather_ingress.get_data(dt_from, dt_to)
        assert response == EXPECTED_OPENWEATHERMAP_HISTORICAL_GET_DATA_RESPONSE


def test_get_data_forecast_api() -> None:
    """Test the get_data method for a scenario where the forecast API would be used"""
    weather_ingress = OpenWeatherDataIngress()
    dt_from = datetime(2024, 1, 5, 16, 1, 1, 1)
    dt_to = dt_from + timedelta(hours=2)
    with requests_mock.Mocker() as m:
        m.get(
            CONST_OPENWEATHERMAP_FORECAST_URL,
            json=MOCKED_CONST_OPENWEATHERMAP_FORECAST_URL_RESPONSE,
        )
        # Override the inferred API base URL to ensure the forecast API is tested.
        # This is required because we're comapring against a mocking result from
        # past dates.
        response = weather_ingress.get_data(
            dt_from,
            dt_to,
            override_inferred_weather_api="forecast",
        )
        assert response == EXPECTED_OPENWEATHERMAP_FORECAST_GET_DATA_RESPONSE
