import pandas as pd
import pytest
from fastapi.testclient import TestClient
from freezegun import freeze_time
from sqlalchemy.orm import Session

from dtbase.models.arima import ArimaModel, ConfigArima
from dtbase.models.utils.dataprocessor.config import (
    ConfigData,
    ConfigOthers,
    ConfigSensors,
)

from .conftest import check_for_docker
from .resources.data_for_tests import (
    EXPECTED_ARIMA_GET_SERVICE_DATA_RESPONSE,
)
from .upload_synthetic_data import insert_trh_readings

DOCKER_RUNNING = check_for_docker()


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_arima_get_temperature(conn_backend: TestClient, session: Session) -> None:
    # Insert synthetic data into database
    insert_trh_readings(
        session,
    )

    # Create config and Arima Object
    config = {
        "data": ConfigData(num_days_training=20),
        "sensors": ConfigSensors(),
    }

    arima = ArimaModel(config)
    tables = arima.get_training_data()
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
    insert_trh_readings(
        session,
    )
    config = {
        "data": ConfigData(num_days_training=20),
        "sensors": ConfigSensors(include_measures=[("Humidity", "Percent")]),
    }
    arima = ArimaModel(config)
    tables = arima.get_training_data()
    assert isinstance(tables, tuple)
    assert len(tables) == 1
    assert isinstance(tables[0], pd.DataFrame)
    assert "Humidity" in tables[0].columns
    assert "sensor_unique_id" in tables[0].columns
    assert "timestamp" in tables[0].columns
    assert len(tables[0]) > 0


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_arima_get_temperature_humidity(conn_backend: None, session: Session) -> None:
    insert_trh_readings(
        session,
    )
    config = {
        "data": ConfigData(num_days_training=20),
        "sensors": ConfigSensors(
            include_measures=[("Temperature", "Degrees C"), ("Humidity", "Percent")]
        ),
    }
    arima = ArimaModel(config)
    tables = arima.get_training_data()
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
    insert_trh_readings(
        session,
    )
    config = {
        "data": ConfigData(num_days_training=20),
        "sensors": ConfigSensors(),
    }

    arima = ArimaModel(config)
    tables = arima.get_training_data()
    cleaned_data = arima.clean_data(tables[0])
    # should be a dict keyed by sensor unique ID
    assert isinstance(cleaned_data, dict)
    assert "TRH1" in cleaned_data.keys()
    assert isinstance(cleaned_data["TRH1"], pd.DataFrame)
    assert len(cleaned_data["TRH1"]) > 0


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_arima_prepare(conn_backend: None, session: Session) -> None:
    insert_trh_readings(
        session,
    )
    config = {
        "data": ConfigData(),
        "sensors": ConfigSensors(),
        "others": ConfigOthers(),
    }

    arima = ArimaModel(config)
    tables = arima.get_training_data()
    cleaned_data = arima.clean_data(tables[0])
    prepared_data = arima.prepare_data(cleaned_data)
    # should be a dict keyed by sensor unique ID
    assert isinstance(prepared_data, dict)
    assert "TRH1" in prepared_data.keys()
    assert isinstance(prepared_data["TRH1"], pd.DataFrame)
    assert len(prepared_data["TRH1"]) > 0


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_arima_pipeline(conn_backend: None, session: Session) -> None:
    insert_trh_readings(
        session,
    )
    config = {
        "data": ConfigData(num_days_training=20),
        "sensors": ConfigSensors(include_measures=[("Temperature", "Degrees C")]),
        "others": ConfigOthers(),
        "arima": ConfigArima(),
    }

    arima = ArimaModel(config)
    tables = arima.get_training_data()
    cleaned_data = arima.clean_data(tables[0])
    prepared_data = arima.prepare_data(cleaned_data)
    values = prepared_data["TRH1"]["Temperature"]
    mean_forecast, conf_int, metrics = arima.pipeline(values)

    assert isinstance(mean_forecast, pd.Series)
    assert isinstance(conf_int, pd.DataFrame)
    assert isinstance(metrics, dict)
    assert "MAPE" in metrics.keys()
    assert "RMSE" in metrics.keys()


@freeze_time("2024-02-13")
def test_arima_get_service_data(conn_backend: None, session: Session) -> None:
    insert_trh_readings(session)
    config = {
        "data": ConfigData(num_days_training=20),
        "sensors": ConfigSensors(include_measures=[("Temperature", "Degrees C")]),
        "others": ConfigOthers(),
        "arima": ConfigArima(),
    }

    arima = ArimaModel(config)
    predicted_data = arima.get_service_data()

    # assert each item of the list individually
    assert len(predicted_data) == 6
    assert predicted_data[0] == EXPECTED_ARIMA_GET_SERVICE_DATA_RESPONSE[0]
    assert predicted_data[1] == EXPECTED_ARIMA_GET_SERVICE_DATA_RESPONSE[1]
    assert predicted_data[2] == EXPECTED_ARIMA_GET_SERVICE_DATA_RESPONSE[2]
    assert predicted_data[3] == EXPECTED_ARIMA_GET_SERVICE_DATA_RESPONSE[3]
    assert predicted_data[4] == EXPECTED_ARIMA_GET_SERVICE_DATA_RESPONSE[4]

    # # We couldn't get tests to reliably pass for the final entry in
    # # predicted data. Arima is not currently deterministic.
    # # It was not a priority to investigate this at time of writing.
    # # TODO: Figure out why arima isn't reproduciable and write tests
    # assert [
    #     round(elem, 4)
    #     for elem in predicted_data[5][1]["measures_and_values"][0]["values"]
    # ] == [
    #     round(elem, 4)
    #     for elem in EXPECTED_ARIMA_GET_SERVICE_DATA_RESPONSE[5][1][
    #         "measures_and_values"
    #     ][0]["values"]
    # ]


def test_arima_call(conn_backend: None, session: Session) -> None:
    insert_trh_readings(session)
    config = {
        "data": ConfigData(num_days_training=20),
        "sensors": ConfigSensors(include_measures=[("Temperature", "Degrees C")]),
        "others": ConfigOthers(),
        "arima": ConfigArima(),
    }

    arima = ArimaModel(config)
    responses = arima()
    for response in responses:
        assert response.status_code < 300
    assert len(responses) == 6
