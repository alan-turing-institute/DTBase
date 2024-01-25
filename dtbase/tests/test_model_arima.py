import pandas as pd
import pytest
from sqlalchemy.orm import Session

from dtbase.models.arima.arima_pipeline import arima_pipeline
from dtbase.models.arima.config import ConfigArima
from dtbase.models.utils.dataprocessor.clean_data import clean_data
from dtbase.models.utils.dataprocessor.config import (
    ConfigData,
    ConfigOthers,
    ConfigSensors,
)
from dtbase.models.utils.dataprocessor.get_data import get_training_data
from dtbase.models.utils.dataprocessor.prepare_data import prepare_data
from dtbase.tests.conftest import AuthenticatedClient, check_for_docker
from dtbase.tests.upload_synthetic_data import insert_trh_readings

DOCKER_RUNNING = check_for_docker()


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_arima_get_temperature(
    conn_backend: AuthenticatedClient, session: Session
) -> None:
    insert_trh_readings(session)
    config = {
        "data": ConfigData(num_days_training=20),
        "sensors": ConfigSensors(),
    }
    tables = get_training_data(config)
    assert isinstance(tables, tuple)
    assert len(tables) == 2
    for table in tables:
        assert isinstance(table, pd.DataFrame)
        assert "sensor_unique_id" in table.columns
        assert "timestamp" in table.columns
        assert len(table) > 0
    assert "Temperature" in tables[0].columns
    assert "Humidity" in tables[1].columns


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_arima_get_humidity(conn_backend: None, session: Session) -> None:
    insert_trh_readings(session)
    config = {
        "data": ConfigData(num_days_training=20),
        "sensors": ConfigSensors(include_measures=[("Humidity", "Percent")]),
    }
    tables = get_training_data(config)
    assert isinstance(tables, tuple)
    assert len(tables) == 1
    assert isinstance(tables[0], pd.DataFrame)
    assert "Humidity" in tables[0].columns
    assert "sensor_unique_id" in tables[0].columns
    assert "timestamp" in tables[0].columns
    assert len(tables[0]) > 0


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_arima_get_temperature_humidity(conn_backend: None, session: Session) -> None:
    insert_trh_readings(session)
    config = {
        "data": ConfigData(num_days_training=20),
        "sensors": ConfigSensors(
            include_measures=[("Temperature", "Degrees C"), ("Humidity", "Percent")]
        ),
    }
    tables = get_training_data(config)
    assert isinstance(tables, tuple)
    assert len(tables) == 2
    assert isinstance(tables[0], pd.DataFrame)
    assert "Temperature" in tables[0].columns
    assert "sensor_unique_id" in tables[0].columns
    assert "timestamp" in tables[0].columns
    assert len(tables[0]) > 0
    assert isinstance(tables[1], pd.DataFrame)
    assert "Humidity" in tables[1].columns
    assert "sensor_unique_id" in tables[1].columns
    assert "timestamp" in tables[1].columns
    assert len(tables[1]) > 0


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_arima_clean(conn_backend: None, session: Session) -> None:
    insert_trh_readings(session)
    config = {
        "data": ConfigData(num_days_training=20),
        "sensors": ConfigSensors(),
    }
    tables = get_training_data(config)
    cleaned_data = clean_data(tables[0], config)
    # should be a dict keyed by sensor unique ID
    assert isinstance(cleaned_data, dict)
    assert "TRH1" in cleaned_data.keys()
    assert isinstance(cleaned_data["TRH1"], pd.DataFrame)
    assert len(cleaned_data["TRH1"]) > 0


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_arima_prepare(conn_backend: None, session: Session) -> None:
    insert_trh_readings(session)
    config = {
        "data": ConfigData(),
        "sensors": ConfigSensors(),
        "others": ConfigOthers(),
    }
    tables = get_training_data(config)
    cleaned_data = clean_data(tables[0], config)
    prepared_data = prepare_data(cleaned_data, config)
    # should be a dict keyed by sensor unique ID
    assert isinstance(prepared_data, dict)
    assert "TRH1" in prepared_data.keys()
    assert isinstance(prepared_data["TRH1"], pd.DataFrame)
    assert len(prepared_data["TRH1"]) > 0


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_arima_pipeline(conn_backend: None, session: Session) -> None:
    insert_trh_readings(session)
    config = {
        "data": ConfigData(num_days_training=20),
        "sensors": ConfigSensors(include_measures=[("Temperature", "Degrees C")]),
        "others": ConfigOthers(),
        "arima": ConfigArima(),
    }
    tables = get_training_data(config)
    cleaned_data = clean_data(tables[0], config)
    prepared_data = prepare_data(cleaned_data, config)
    values = prepared_data["TRH1"]["Temperature"]
    mean_forecast, conf_int, metrics = arima_pipeline(values, config["arima"])
    assert isinstance(mean_forecast, pd.Series)
    assert isinstance(conf_int, pd.DataFrame)
    assert isinstance(metrics, dict)
    assert "MAPE" in metrics.keys()
    assert "RMSE" in metrics.keys()
