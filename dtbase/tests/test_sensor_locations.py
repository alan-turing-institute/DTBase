"""
Test the functions for accessing the sensor location table.
"""
import datetime as dt

from dtbase.core import sensor_locations
from dtbase.tests import test_locations, test_sensors

COORDINATES1 = {
    "latitude": test_locations.LATITUDE1,
    "longitude": test_locations.LONGITUDE1,
}
COORDINATES2 = {"latitude": test_locations.LATITUDE3}
DATE1 = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=2)
DATE2 = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=1)


def insert_sensors_and_locations(session):
    """Insert some sensors and locations."""
    test_sensors.insert_sensors(session)
    test_locations.insert_locations(session)


def insert_sensor_locations(session):
    """Insert some sensor locations."""
    uniq_id = test_sensors.SENSOR_ID1
    sensor_locations.insert_sensor_location(
        uniq_id, "latlong", COORDINATES1, DATE1, session=session
    )


def test_insert_sensor_locations(session):
    """Test inserting sensor locations."""
    insert_sensors_and_locations(session)
    insert_sensor_locations(session)


def test_get_sensor_locations(session):
    """Test getting sensor locations."""
    insert_sensors_and_locations(session)
    uniq_id = test_sensors.SENSOR_ID1
    locations = sensor_locations.get_location_history(uniq_id, session=session)
    assert len(locations) == 0

    insert_sensor_locations(session)
    locations = sensor_locations.get_location_history(uniq_id, session=session)
    assert len(locations) == 1
    assert all(locations[0][k] == v for k, v in COORDINATES1.items())
    assert locations[0]["installation_datetime"] == DATE1
    sensor_locations.insert_sensor_location(
        uniq_id, "lat only", COORDINATES2, DATE2, session=session
    )
    locations = sensor_locations.get_location_history(uniq_id, session=session)
    assert len(locations) == 2
    assert all(locations[0][k] == v for k, v in COORDINATES2.items())
    assert locations[0]["installation_datetime"] == DATE2
