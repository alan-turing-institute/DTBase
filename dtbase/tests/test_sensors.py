"""
Test the functions for accessing the sensor tables.
"""
import datetime as dt

import sqlalchemy
import pytest

from dtbase.core import sensors

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Functions for inserting some data into the database. These will called at the
# beginning of many tests to populate the database with data to test against. They are a
# lot like fixtures, but aren't fixtures because running them successfully is a test in
# itself.

# Some example values used for testing.
SENSOR_ID1 = "ABCSERIALNUMBER"
SENSOR_ID2 = "FAKEUUIDISFAKE"
TEMPERATURES = [0.0, 1.0, 2.0]
TIMESTAMPS = list(
    map(
        lambda x: dt.datetime.strptime(x, "%Y-%m-%d"),
        ["2022-10-10", "2022-10-11", "2022-10-12"],
    )
)


def insert_measures(session):
    """Insert some sensor measures into the database."""
    sensors.insert_sensor_measure(
        name="temperature", units="Kelvin", datatype="float", session=session
    )
    sensors.insert_sensor_measure(
        name="is raining", units="", datatype="boolean", session=session
    )


def insert_type(session):
    """Insert a sensor type into the database."""
    insert_measures(session)
    sensors.insert_sensor_type(
        name="weather",
        description="Weather sensor for temperature and rain",
        measures=["temperature", "is raining"],
        session=session,
    )


def insert_sensors(session):
    """Insert some sensors into the database."""
    insert_type(session)
    sensors.insert_sensor(
        "weather",
        SENSOR_ID1,
        name="Roof weather sensor",
        notes="Located at the northeast corner, under the bucket.",
        session=session,
    )
    sensors.insert_sensor("weather", SENSOR_ID2, session=session)


def insert_readings(session):
    """Insert some sensor readings into the database."""
    insert_sensors(session)
    sensors.insert_sensor_readings(
        "temperature",
        SENSOR_ID1,
        TEMPERATURES,
        TIMESTAMPS,
        session=session,
    )


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Tests for sensor measures


def test_insert_sensor_measure(rollback_session):
    """Test inserting sensor measures."""
    insert_measures(rollback_session)


def test_insert_sensor_measure_duplicate(rollback_session):
    """Try to insert a sensor measure that conflicts with one that exists."""
    sensors.insert_sensor_measure(
        name="temperature", units="Kelvin", datatype="float", session=rollback_session
    )
    # This is fine, because the units are different.
    sensors.insert_sensor_measure(
        name="temperature", units="Celsius", datatype="float", session=rollback_session
    )
    # This is a duplicate.
    error_msg = (
        "duplicate key value violates unique constraint "
        '"sensor_measure_name_units_key"'
    )
    with pytest.raises(sqlalchemy.exc.IntegrityError, match=error_msg):
        sensors.insert_sensor_measure(
            name="temperature",
            units="Kelvin",
            datatype="integer",
            session=rollback_session,
        )


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Tests for sensor types


def test_insert_sensor_type(rollback_session):
    """Test inserting a sensor type."""
    insert_type(rollback_session)


def test_insert_sensor_type_duplicate(rollback_session):
    """Try to insert a sensor type that conflicts with one that exists."""
    insert_type(rollback_session)
    error_msg = 'duplicate key value violates unique constraint "sensor_type_name_key"'
    with pytest.raises(sqlalchemy.exc.IntegrityError, match=error_msg):
        sensors.insert_sensor_type(
            name="weather",
            description="The description can be different.",
            measures=["temperature"],
            session=rollback_session,
        )


def test_insert_sensor_type_no_measurer(rollback_session):
    """Try to insert a sensor type that uses measures that don't exist."""
    insert_type(rollback_session)
    error_msg = "No sensor measure named 'is raining misspelled'"
    with pytest.raises(ValueError, match=error_msg):
        sensors.insert_sensor_type(
            name="weather misspelled",
            description="Temperature and rain misspelled",
            measures=["temperature", "is raining misspelled"],
            session=rollback_session,
        )


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Tests for sensors


def test_insert_sensor(rollback_session):
    """Test inserting sensors."""
    insert_sensors(rollback_session)


def test_insert_sensor_duplicate(rollback_session):
    """Try to insert a sensor that already exists."""
    insert_sensors(rollback_session)
    error_msg = (
        'duplicate key value violates unique constraint "sensor_unique_identifier_key"'
    )
    with pytest.raises(sqlalchemy.exc.IntegrityError, match=error_msg):
        sensors.insert_sensor("weather", SENSOR_ID1, session=rollback_session)


def test_insert_sensor_no_type(rollback_session):
    """Try to insert a sensor with a non-existing type."""
    insert_type(rollback_session)
    with pytest.raises(ValueError, match="No sensor type named 'electron microscope'"):
        sensors.insert_sensor(
            "electron microscope", "BLAHBLAHBLAH", session=rollback_session
        )


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Tests for sensor readings


def test_insert_sensor_readings(rollback_session):
    """Test inserting sensor readings"""
    insert_readings(rollback_session)
    read_readings = sensors.get_sensor_readings(
        "temperature",
        SENSOR_ID1,
        dt_from=TIMESTAMPS[0],
        dt_to=TIMESTAMPS[-1],
        session=rollback_session,
    )
    assert read_readings == list(zip(TEMPERATURES, TIMESTAMPS))


def test_read_partial_sensor_readings(rollback_session):
    """Test inserting sensor readings"""
    insert_readings(rollback_session)
    # Read all except first reading.
    read_readings = sensors.get_sensor_readings(
        "temperature",
        SENSOR_ID1,
        dt_from=TIMESTAMPS[1],
        dt_to=TIMESTAMPS[-1],
        session=rollback_session,
    )
    assert read_readings == list(zip(TEMPERATURES[1:], TIMESTAMPS[1:]))


def test_insert_sensor_readings_wrong_measure(rollback_session):
    """Try to insert sensor readings with the wrong measure."""
    insert_sensors(rollback_session)
    error_msg = (
        "Measure 'temperature misspelled' is not a valid measure for sensor "
        f"'{SENSOR_ID1}'."
    )
    with pytest.raises(ValueError, match=error_msg):
        sensors.insert_sensor_readings(
            "temperature misspelled",
            SENSOR_ID1,
            TEMPERATURES,
            TIMESTAMPS,
            session=rollback_session,
        )


def test_insert_sensor_readings_wrong_number(rollback_session):
    """Try to insert too few or too many sensor readings."""
    insert_sensors(rollback_session)
    error_msg = (
        "There should be as many readings as there are timestamps, but got 4 and 3"
    )
    with pytest.raises(ValueError, match=error_msg):
        sensors.insert_sensor_readings(
            "temperature",
            SENSOR_ID1,
            TEMPERATURES + [23.0],
            TIMESTAMPS,
            session=rollback_session,
        )
    error_msg = (
        "There should be as many readings as there are timestamps, but got 2 and 3"
    )
    with pytest.raises(ValueError, match=error_msg):
        sensors.insert_sensor_readings(
            "temperature",
            SENSOR_ID1,
            TEMPERATURES[:-1],
            TIMESTAMPS,
            session=rollback_session,
        )


def test_insert_sensor_readings_wrong_type(rollback_session):
    """Try to insert sensor readings of the wrong type."""
    insert_sensors(rollback_session)
    error_msg = (
        "For sensor measure 'temperature' expected a readings of type float "
        "but got a <class 'bool'>."
    )
    with pytest.raises(ValueError, match=error_msg):
        sensors.insert_sensor_readings(
            "temperature",
            SENSOR_ID1,
            [True, False, False],
            TIMESTAMPS,
            session=rollback_session,
        )
    error_msg = (
        'column "timestamp" is of type timestamp without time zone but '
        "expression is of type boolean"
    )
    with pytest.raises(sqlalchemy.exc.ProgrammingError, match=error_msg):
        sensors.insert_sensor_readings(
            "temperature",
            SENSOR_ID1,
            TEMPERATURES,
            [True, False, False],
            session=rollback_session,
        )


def test_insert_sensor_readings_duplicate(rollback_session):
    """Try to insert sensor readings of the wrong type."""
    insert_readings(rollback_session)
    error_msg = (
        "duplicate key value violates unique constraint "
        '"sensor_float_reading_measure_id_sensor_id_timestamp_key"'
    )
    with pytest.raises(sqlalchemy.exc.IntegrityError, match=error_msg):
        sensors.insert_sensor_readings(
            "temperature",
            SENSOR_ID1,
            [23.0, 23.0, 23.0],
            TIMESTAMPS,
            session=rollback_session,
        )


# def test_list_sensors(rollback_session):
#    """Find the inserted sensors."""
#    insert_sensors(rollback_session)
#    all_sensors = sensors.list_sensors("weather", session=rollback_session)
#    assert len(all_sensors) == 2
#    assert all_sensors[0]["temperature"] == LATITUDE1
#    assert all_sensors[0]["longitude"] == LONGITUDE1
#    assert all_sensors[1]["temperature"] == LATITUDE2
#    assert all_sensors[1]["longitude"] == LONGITUDE2
#    some_sensors = sensors.list_sensors(
#        "weather", session=rollback_session, temperature=LATITUDE1
#    )
#    assert len(some_sensors) == 1
#    assert some_sensors[0]["temperature"] == LATITUDE1
#    assert some_sensors[0]["longitude"] == LONGITUDE1
#    no_sensors = sensors.list_sensors(
#        "weather", session=rollback_session, temperature=-3.0
#    )
#    assert len(no_sensors) == 0
#
#
# def test_delete_sensor(rollback_session):
#    """Delete a sensor, and check that it is deleted and can't be redeleted."""
#    insert_sensors(rollback_session)
#    sensors.delete_sensor_by_coordinates(
#        "weather", temperature=LATITUDE2, longitude=LONGITUDE2, session=rollback_session
#    )
#    all_sensors = sensors.list_sensors("weather", session=rollback_session)
#    assert len(all_sensors) == 1
#
#    # Doing the same deletion again should fail, since that row is gone.
#    error_msg = (
#        "Location not found: weather, "
#        f"{{'temperature': {LATITUDE2}, 'longitude': {LONGITUDE2}}}"
#    )
#    with pytest.raises(ValueError, match=error_msg):
#        sensors.delete_sensor_by_coordinates(
#            "weather",
#            temperature=LATITUDE2,
#            longitude=LONGITUDE2,
#            session=rollback_session,
#        )
#
#    sensors.delete_sensor_by_coordinates(
#        "weather", temperature=LATITUDE1, longitude=LONGITUDE1, session=rollback_session
#    )
#    all_sensors = sensors.list_sensors("weather", session=rollback_session)
#    assert len(all_sensors) == 0
#
#
# def test_delete_sensor_nonexistent(rollback_session):
#    """Try to delete a non-existent sensor."""
#    insert_sensors(rollback_session)
#    error_msg = "Location not found: weather, {'temperature': 0.0, 'longitude': 0.0}"
#    with pytest.raises(ValueError, match=error_msg):
#        sensors.delete_sensor_by_coordinates(
#            "weather", temperature=0.0, longitude=0.0, session=rollback_session
#        )
