"""
Test the functions for accessing the sensor tables.
"""
import datetime as dt

import sqlalchemy as sqla
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
SENSOR_ID3 = "STRINGSTRINGSTRING"
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


def insert_types(session):
    """Insert a sensor type into the database."""
    insert_measures(session)
    sensors.insert_sensor_type(
        name="weather",
        description="Weather sensor for temperature and rain",
        measures=["temperature", "is raining"],
        session=session,
    )
    sensors.insert_sensor_type(
        name="temperature",
        description="Temperature sensor",
        measures=["temperature"],
        session=session,
    )


def insert_sensors(session):
    """Insert some sensors into the database."""
    insert_types(session)
    sensors.insert_sensor(
        "weather",
        SENSOR_ID1,
        name="Roof weather sensor",
        notes="Located at the northeast corner, under the bucket.",
        session=session,
    )
    sensors.insert_sensor("weather", SENSOR_ID2, session=session)
    sensors.insert_sensor("temperature", SENSOR_ID3, session=session)


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
    with pytest.raises(sqla.exc.IntegrityError, match=error_msg):
        sensors.insert_sensor_measure(
            name="temperature",
            units="Kelvin",
            datatype="integer",
            session=rollback_session,
        )


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Tests for sensor types


def test_insert_sensor_types(rollback_session):
    """Test inserting a sensor type."""
    insert_types(rollback_session)


def test_insert_sensor_types_duplicate(rollback_session):
    """Try to insert a sensor type that conflicts with one that exists."""
    insert_types(rollback_session)
    error_msg = 'duplicate key value violates unique constraint "sensor_type_name_key"'
    with pytest.raises(sqla.exc.IntegrityError, match=error_msg):
        sensors.insert_sensor_type(
            name="weather",
            description="The description can be different.",
            measures=["temperature"],
            session=rollback_session,
        )


def test_insert_sensor_types_no_measurer(rollback_session):
    """Try to insert a sensor type that uses measures that don't exist."""
    insert_types(rollback_session)
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
    with pytest.raises(sqla.exc.IntegrityError, match=error_msg):
        sensors.insert_sensor("weather", SENSOR_ID1, session=rollback_session)


def test_insert_sensor_no_type(rollback_session):
    """Try to insert a sensor with a non-existing type."""
    insert_types(rollback_session)
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
    with pytest.raises(sqla.exc.ProgrammingError, match=error_msg):
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
    with pytest.raises(sqla.exc.IntegrityError, match=error_msg):
        sensors.insert_sensor_readings(
            "temperature",
            SENSOR_ID1,
            [23.0, 23.0, 23.0],
            TIMESTAMPS,
            session=rollback_session,
        )


def test_list_sensors(rollback_session):
    """Find the inserted sensors."""
    insert_sensors(rollback_session)
    all_sensors = sensors.list_sensors(session=rollback_session)
    expected_keys = {
        "id",
        "name",
        "unique_identifier",
        "notes",
        "sensor_type_id",
        "sensor_type_name",
    }
    assert len(all_sensors) == 3
    assert all_sensors[0]["unique_identifier"] == SENSOR_ID1
    assert set(all_sensors[0].keys()) == expected_keys
    assert all_sensors[0]["sensor_type_name"] == "weather"
    assert all_sensors[1]["unique_identifier"] == SENSOR_ID2
    assert all_sensors[1]["sensor_type_name"] == "weather"
    assert all_sensors[2]["unique_identifier"] == SENSOR_ID3
    assert all_sensors[2]["sensor_type_name"] == "temperature"
    weather_sensors = sensors.list_sensors("weather", session=rollback_session)
    assert len(weather_sensors) == 2
    assert weather_sensors[0]["unique_identifier"] == SENSOR_ID1
    assert weather_sensors[0]["sensor_type_name"] == "weather"
    assert weather_sensors[1]["unique_identifier"] == SENSOR_ID2
    assert weather_sensors[1]["sensor_type_name"] == "weather"


def test_list_sensor_measures(rollback_session):
    """Find the inserted sensor measures."""
    insert_measures(rollback_session)
    all_measures = sensors.list_sensor_measures(session=rollback_session)
    expected_keys = {"id", "name", "units", "datatype"}
    assert len(all_measures) == 2
    assert all_measures[0]["name"] == "temperature"
    assert set(all_measures[0].keys()) == expected_keys
    assert all_measures[1]["name"] == "is raining"


def test_list_sensor_types(rollback_session):
    """Find the inserted sensor types."""
    insert_types(rollback_session)
    all_types = sensors.list_sensor_types(session=rollback_session)
    expected_keys = {"id", "name", "description", "measures"}
    assert len(all_types) == 2
    assert all_types[0]["name"] == "weather"
    assert {"name": "temperature", "units": "Kelvin", "datatype": "float"} in all_types[
        0
    ]["measures"]
    assert set(all_types[0].keys()) == expected_keys
    assert all_types[1]["name"] == "temperature"


def test_delete_sensor_measure(rollback_session):
    """Delete a sensor measure, and check that it is deleted and can't be redeleted."""
    insert_measures(rollback_session)
    sensors.delete_sensor_measure("temperature", session=rollback_session)
    all_measures = sensors.list_sensor_measures(session=rollback_session)
    assert len(all_measures) == 1

    # Doing the same deletion again should fail, since that row is gone.
    error_msg = "No sensor measure named 'temperature'"
    with pytest.raises(ValueError, match=error_msg):
        sensors.delete_sensor_measure("temperature", session=rollback_session)


def test_delete_sensor_type_readings_exists(rollback_session):
    """Try to delete a sensor measure for which a sensor type exists."""
    insert_types(rollback_session)
    error_msg = (
        'update or delete on table "sensor_measure" violates foreign key constraint '
        '"sensor_type_measure_relation_measure_id_fkey" on table '
        '"sensor_type_measure_relation"'
    )
    with pytest.raises(sqla.exc.IntegrityError, match=error_msg):
        sensors.delete_sensor_measure("temperature", session=rollback_session)


def test_delete_sensor_type(rollback_session):
    """Delete a sensor type, and check that it is deleted and can't be redeleted."""
    insert_types(rollback_session)
    sensors.delete_sensor_type("weather", session=rollback_session)
    all_types = sensors.list_sensor_types(session=rollback_session)
    assert len(all_types) == 1

    # Doing the same deletion again should fail, since that row is gone.
    error_msg = "No sensor type named 'weather'"
    with pytest.raises(ValueError, match=error_msg):
        sensors.delete_sensor_type("weather", session=rollback_session)


def test_delete_sensor_type_sensor_exists(rollback_session):
    """Try to delete a sensor type for which a sensor exists."""
    insert_sensors(rollback_session)
    error_msg = (
        'update or delete on table "sensor_type" violates foreign key '
        'constraint "sensor_type_id_fkey" on table "sensor"'
    )
    with pytest.raises(sqla.exc.IntegrityError, match=error_msg):
        sensors.delete_sensor_type("weather", session=rollback_session)


def test_delete_sensor(rollback_session):
    """Delete a sensor, and check that it is deleted and can't be redeleted."""
    insert_sensors(rollback_session)
    sensors.delete_sensor(SENSOR_ID1, session=rollback_session)
    all_sensors = sensors.list_sensors(session=rollback_session)
    assert len(all_sensors) == 2

    # Doing the same deletion again should fail, since that row is gone.
    error_msg = f"No sensor '{SENSOR_ID1}'"
    with pytest.raises(ValueError, match=error_msg):
        sensors.delete_sensor(SENSOR_ID1, session=rollback_session)


def test_delete_sensor_nonexistent(rollback_session):
    """Try to delete a non-existent sensor."""
    insert_sensors(rollback_session)
    error_msg = "No sensor 'BLAHBLAH'"
    with pytest.raises(ValueError, match=error_msg):
        sensors.delete_sensor("BLAHBLAH", session=rollback_session)
