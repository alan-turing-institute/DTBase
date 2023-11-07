"""
Sample code to insert two sensors (each with two measures) together with
corresponding dummy measurements
"""

from dtbase.core.utils import get_db_session
from dtbase.tests.upload_synthetic_data import insert_trh_readings

session = get_db_session()
insert_trh_readings(session, sensor_unique_id="TRH1")
insert_trh_readings(session, sensor_unique_id="TRH2")
