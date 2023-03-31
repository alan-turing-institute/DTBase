import pytest
import pandas as pd
from dtbase.tests.upload_synthetic_data import insert_trh_readings
from dtbase.models.utils.get_data import get_training_data
from dtbase.models.arima.arima.clean_data import clean_data
from dtbase.tests.conftest import check_for_docker

DOCKER_RUNNING = check_for_docker()


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_arima_clean(session):
    insert_trh_readings(session)
    tables = get_training_data(
        measures={"Temperature": ["TRH1"]},
        delta_days=20,
        session=session
    )
    cleaned_data = clean_data(tables[0])
    # should be a dict keyed by sensor unique ID
    assert isinstance(cleaned_data, dict)
    assert "TRH1" in cleaned_data.keys()
    assert isinstance(cleaned_data["TRH1"], pd.DataFrame)
    assert len(cleaned_data["TRH1"]) > 0
