'''
Sample code to insert two sensors (each with two measures) together with
corresponding dummy measurements
'''

from dtbase.core.utils import *
from dtbase.tests.upload_synthetic_data import *
session = get_db_session()
insert_trh_readings(session, sensor_unique_id="TRH1")
insert_trh_readings(session, sensor_unique_id="TRH2", measure_suffix="_s2")
