"""
Test the functions for accessing the sensor location table.
"""
import datetime as dt

from dtbase.core import sensor_locations
from dtbase.tests import test_locations, test_sensors


def test_sensor_locations(session):
    """Test inserting and getting sensor locations."""
    test_sensors.insert_sensors(session)
    test_locations.insert_locations(session)
    uniq_id = test_sensors.SENSOR_ID1
    locations = sensor_locations.get_location_history(uniq_id, session=session)
    assert len(locations) == 0

    coordinates1 = {
        "latitude": test_locations.LATITUDE1,
        "longitude": test_locations.LONGITUDE1,
    }
    date1 = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=2)
    sensor_locations.insert_sensor_location(
        uniq_id, "latlong", coordinates1, date1, session=session
    )
    locations = sensor_locations.get_location_history(uniq_id, session=session)
    assert len(locations) == 1
    print([locations[0][k] == v for k, v in coordinates1.items()])
    assert all(locations[0][k] == v for k, v in coordinates1.items())
    assert locations[0]["installation_datetime"] == date1

    coordinates2 = {"latitude": test_locations.LATITUDE3}
    date2 = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=1)
    sensor_locations.insert_sensor_location(
        uniq_id, "lat only", coordinates2, date2, session=session
    )
    locations = sensor_locations.get_location_history(uniq_id, session=session)
    assert len(locations) == 2
    assert all(locations[0][k] == v for k, v in coordinates2.items())
    assert locations[0]["installation_datetime"] == date2
