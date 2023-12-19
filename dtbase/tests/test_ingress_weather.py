from datetime import datetime, timedelta

import pytest

from dtbase.core.constants import (
    CONST_OPENWEATHERMAP_FORECAST_URL,
    CONST_OPENWEATHERMAP_HISTORICAL_URL,
)
from dtbase.ingress.ingress_weather import (
    SENSOR_OPENWEATHERMAPFORECAST,
    SENSOR_OPENWEATHERMAPHISTORICAL,
    OpenWeatherDataIngress,
)

NOW = datetime.now()


@pytest.mark.parametrize(
    "dt_from, dt_to, expected",
    [
        (
            NOW - timedelta(hours=72),
            "present",
            (CONST_OPENWEATHERMAP_HISTORICAL_URL, SENSOR_OPENWEATHERMAPHISTORICAL),
        ),
        (
            "present",
            NOW + timedelta(days=1),
            (CONST_OPENWEATHERMAP_FORECAST_URL, SENSOR_OPENWEATHERMAPFORECAST),
        ),
    ],
)
def test_get_api_base_url_and_sensor_name(
    dt_from: datetime, dt_to: datetime, expected: tuple[str, str]
) -> None:
    weather_ingress = OpenWeatherDataIngress()
    assert weather_ingress.get_api_base_url_and_sensor(dt_from, dt_to) == expected


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
def test_get_api_base_url_and_sensor_name_raises(
    dt_from: datetime, dt_to: datetime, expected: ValueError
) -> None:
    weather_ingress = OpenWeatherDataIngress()
    with pytest.raises(expected):
        weather_ingress.get_api_base_url_and_sensor(dt_from, dt_to)
