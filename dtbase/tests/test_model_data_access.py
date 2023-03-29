import pytest
from dtbase.tests.upload_synthetic_data import insert_trh_readings
from dtbase.models.utils.get_data import get_training_data


def test_get_temperature(session):
    insert_trh_readings(session)
    pass
