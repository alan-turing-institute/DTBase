import pandas as pd
import pytest
from sqlalchemy.orm import Session

from dtbase.models.arima.arima.arima_pipeline import arima_pipeline
from dtbase.models.utils.dataprocessor.clean_data import clean_data
from dtbase.models.utils.dataprocessor.get_data import get_training_data
from dtbase.models.utils.dataprocessor.prepare_data import prepare_data
from dtbase.tests.conftest import check_for_docker
from dtbase.tests.upload_synthetic_data import insert_trh_readings

DOCKER_RUNNING = check_for_docker()


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_arima_get_temperature(session: Session) -> None:
    insert_trh_readings(session)
    tables = get_training_data(delta_days=20, session=session)
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
def test_arima_get_humidity(session: Session) -> None:
    insert_trh_readings(session)
    tables = get_training_data(
        measures_list=[("Humidity", "Percent")], delta_days=20, session=session
    )
    assert isinstance(tables, tuple)
    assert len(tables) == 1
    assert isinstance(tables[0], pd.DataFrame)
    assert "Humidity" in tables[0].columns
    assert "sensor_unique_id" in tables[0].columns
    assert "timestamp" in tables[0].columns
    assert len(tables[0]) > 0


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_arima_get_temperature_humidity(session: Session) -> None:
    insert_trh_readings(session)
    tables = get_training_data(
        measures_list=[("Temperature", "Degrees"), ("Humidity", "Percent")],
        delta_days=20,
        session=session,
    )
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
def test_arima_clean(session: Session) -> None:
    insert_trh_readings(session)
    tables = get_training_data(delta_days=20, session=session)
    cleaned_data = clean_data(tables[0])
    # should be a dict keyed by sensor unique ID
    assert isinstance(cleaned_data, dict)
    assert "TRH1" in cleaned_data.keys()
    assert isinstance(cleaned_data["TRH1"], pd.DataFrame)
    assert len(cleaned_data["TRH1"]) > 0


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_arima_prepare(session: Session) -> None:
    insert_trh_readings(session)
    tables = get_training_data(delta_days=20, session=session)
    cleaned_data = clean_data(tables[0])
    prepared_data = prepare_data(cleaned_data)
    # should be a dict keyed by sensor unique ID
    assert isinstance(prepared_data, dict)
    assert "TRH1" in prepared_data.keys()
    assert isinstance(prepared_data["TRH1"], pd.DataFrame)
    assert len(prepared_data["TRH1"]) > 0


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_arima_pipeline(session: Session) -> None:
    insert_trh_readings(session)
    tables = get_training_data(
        measures_list=[("Temperature", "Degrees")], delta_days=20, session=session
    )
    cleaned_data = clean_data(tables[0])
    prepared_data = prepare_data(cleaned_data)
    values = prepared_data["TRH1"]["Temperature"]
    mean_forecast, conf_int, metrics = arima_pipeline(values)
    assert isinstance(mean_forecast, pd.Series)
    assert isinstance(conf_int, pd.DataFrame)
    assert isinstance(metrics, dict)
    assert "MAPE" in metrics.keys()
    assert "RMSE" in metrics.keys()
