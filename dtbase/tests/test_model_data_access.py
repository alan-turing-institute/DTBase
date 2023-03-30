import pytest
import pandas as pd
from dtbase.tests.upload_synthetic_data import insert_trh_readings
from dtbase.models.utils.get_data import get_training_data


def test_get_temperature(session):
    insert_trh_readings(session)
    tables = get_training_data(
        measures={"Temperature": ["TRH1"]},
        delta_days=20,
        session=session
    )
    assert isinstance(tables, tuple)
    assert len(tables) == 1
    assert isinstance(tables[0], pd.DataFrame)
    assert "Temperature" in tables[0].columns
    assert "sensor_unique_id" in tables[0].columns
    assert "timestamp" in tables[0].columns
    assert len(tables[0]) > 0
