"""
Test the functions for accessing the sensor tables.
"""
import datetime as dt

import pytest
from sqlalchemy.exc import IntegrityError, ProgrammingError
from sqlalchemy.orm import Session

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
        dt.datetime.fromisoformat,
        [
            "2022-10-10T01:00:00+00:00",
            "2022-10-11T01:00:00+00:00",
            "2022-10-12T01:00:00+00:00",
        ],
    )
)


def insert_measures(dbsession: Session) -> None:
    """Insert some sensor measures into the database."""
    sensors.insert_sensor_measure(
        name="temperature", units="Kelvin", datatype="float", session=dbsession
    )
    sensors.insert_sensor_measure(
        name="is raining", units="", datatype="boolean", session=dbsession
    )


def insert_types(dbsession: Session) -> None:
    """Insert a sensor type into the database."""
    insert_measures(dbsession)
    sensors.insert_sensor_type(
        name="weather",
        description="Weather sensor for temperature and rain",
        measures=[
            {"name": "temperature", "units": "Kelvin", "datatype": "float"},
            {"name": "is raining", "units": "", "datatype": "boolean"},
        ],
        session=dbsession,
    )
    sensors.insert_sensor_type(
        name="temperature",
        description="Temperature sensor",
        measures=[{"name": "temperature", "units": "Kelvin", "datatype": "float"}],
        session=dbsession,
    )


def insert_sensors(dbsession: Session) -> None:
    """Insert some sensors into the database."""
    insert_types(dbsession)
    sensors.insert_sensor(
        "weather",
        SENSOR_ID1,
        name="Roof weather sensor",
        notes="Located at the northeast corner, under the bucket.",
        session=dbsession,
    )
    sensors.insert_sensor("weather", SENSOR_ID2, session=dbsession)
    sensors.insert_sensor("temperature", SENSOR_ID3, session=dbsession)


def insert_readings(dbsession: Session) -> None:
    """Insert some sensor readings into the database."""
    insert_sensors(dbsession)
    sensors.insert_sensor_readings(
        "temperature",
        SENSOR_ID1,
        TEMPERATURES,
        TIMESTAMPS,
        session=dbsession,
    )


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Tests for sensor measures


def test_insert_sensor_measure(session: Session) -> None:
    """Test inserting sensor measures."""
    insert_measures(session)


def test_insert_sensor_measure_duplicate(session: Session) -> None:
    """Try to insert a sensor measure that conflicts with one that exists."""
    sensors.insert_sensor_measure(
        name="temperature", units="Kelvin", datatype="float", session=session
    )
    # This is fine, because the units are different.
    sensors.insert_sensor_measure(
        name="temperature", units="Celsius", datatype="float", session=session
    )
    # This is a duplicate.
    error_msg = (
        "duplicate key value violates unique constraint "
        '"sensor_measure_name_units_key"'
    )
    with pytest.raises(IntegrityError, match=error_msg):
        sensors.insert_sensor_measure(
            name="temperature",
            units="Kelvin",
            datatype="integer",
            session=session,
        )


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Tests for sensor types


def test_insert_sensor_types(session: Session) -> None:
    """Test inserting a sensor type."""
    insert_types(session)


def test_insert_sensor_types_duplicate(session: Session) -> None:
    """Try to insert a sensor type that conflicts with one that exists."""
    insert_types(session)

    error_msg = 'duplicate key value violates unique constraint "sensor_type_name_key"'
    with pytest.raises(IntegrityError, match=error_msg):
        sensors.insert_sensor_type(
            name="weather",
            description="The description can be different.",
            measures=["temperature"],
            session=session,
        )


def test_insert_sensor_types_no_measure(session: Session) -> None:
    """Try to insert a sensor type that uses measures that don't exist."""
    insert_types(session)
    error_msg = "No sensor measure named 'is raining misspelled'"
    with pytest.raises(ValueError, match=error_msg):
        sensors.insert_sensor_type(
            name="weather misspelled",
            description="Temperature and rain misspelled",
            measures=[
                {"name": "temperature", "units": "Kelvin"},
                {"name": "is raining misspelled", "units": ""},
            ],
            session=session,
        )


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Tests for sensors


def test_insert_sensor(session: Session) -> None:
    """Test inserting sensors."""
    insert_sensors(session)


def test_insert_sensor_duplicate(session: Session) -> None:
    """Try to insert a sensor that already exists."""
    insert_sensors(session)
    error_msg = (
        'duplicate key value violates unique constraint "sensor_unique_identifier_key"'
    )
    with pytest.raises(IntegrityError, match=error_msg):
        sensors.insert_sensor("weather", SENSOR_ID1, session=session)


def test_insert_sensor_no_type(session: Session) -> None:
    """Try to insert a sensor with a non-existing type."""
    insert_types(session)
    with pytest.raises(ValueError, match="No sensor type named 'electron microscope'"):
        sensors.insert_sensor("electron microscope", "BLAHBLAHBLAH", session=session)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Tests for sensor readings


def test_insert_sensor_readings(session: Session) -> None:
    """Test inserting sensor readings"""
    insert_readings(session)
    read_readings = sensors.get_sensor_readings(
        "temperature",
        SENSOR_ID1,
        dt_from=TIMESTAMPS[0],
        dt_to=TIMESTAMPS[-1],
        session=session,
    )
    assert read_readings == list(zip(TEMPERATURES, TIMESTAMPS))


def test_read_partial_sensor_readings(session: Session) -> None:
    """Test inserting sensor readings"""
    insert_readings(session)
    # Read all except first reading.
    read_readings = sensors.get_sensor_readings(
        "temperature",
        SENSOR_ID1,
        dt_from=TIMESTAMPS[1],
        dt_to=TIMESTAMPS[-1],
        session=session,
    )
    assert read_readings == list(zip(TEMPERATURES[1:], TIMESTAMPS[1:]))


def test_insert_sensor_readings_wrong_measure(session: Session) -> None:
    """Try to insert sensor readings with the wrong measure."""
    insert_sensors(session)
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
            session=session,
        )


def test_insert_sensor_readings_wrong_number(session: Session) -> None:
    """Try to insert too few or too many sensor readings."""
    insert_sensors(session)
    error_msg = (
        "There should be as many readings as there are timestamps, but got 4 and 3"
    )
    with pytest.raises(ValueError, match=error_msg):
        sensors.insert_sensor_readings(
            "temperature",
            SENSOR_ID1,
            TEMPERATURES + [23.0],
            TIMESTAMPS,
            session=session,
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
            session=session,
        )


def test_insert_sensor_readings_wrong_type(session: Session) -> None:
    """Try to insert sensor readings of the wrong type."""
    insert_sensors(session)
    error_msg = (
        "For sensor measure 'temperature' expected readings of type float "
        "but got a <class 'bool'>."
    )
    with pytest.raises(ValueError, match=error_msg):
        sensors.insert_sensor_readings(
            "temperature",
            SENSOR_ID1,
            [True, False, False],
            TIMESTAMPS,
            session=session,
        )
    error_msg = (
        'column "timestamp" is of type timestamp with time zone but '
        "expression is of type boolean"
    )
    with pytest.raises(ProgrammingError, match=error_msg):
        sensors.insert_sensor_readings(
            "temperature",
            SENSOR_ID1,
            TEMPERATURES,
            [True, False, False],
            session=session,
        )


def test_insert_sensor_readings_duplicate(session: Session) -> None:
    """Test that we can insert sensor readings that include some that have already been
    inserted.
    """
    insert_readings(session)
    new_time = dt.datetime.fromisoformat("2022-10-13T01:00:00+00:00")
    sensors.insert_sensor_readings(
        "temperature",
        SENSOR_ID1,
        TEMPERATURES + [23.0],
        TIMESTAMPS + [new_time],
        session=session,
    )
    read_readings = sensors.get_sensor_readings(
        "temperature",
        SENSOR_ID1,
        dt_from=TIMESTAMPS[0],
        dt_to=new_time,
        session=session,
    )
    assert len(read_readings) == len(TIMESTAMPS) + 1


def test_list_sensors(session: Session) -> None:
    """Find the inserted sensors."""
    insert_sensors(session)
    all_sensors = sensors.list_sensors(session=session)
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
    weather_sensors = sensors.list_sensors(type_name="weather", session=session)
    assert len(weather_sensors) == 2
    assert weather_sensors[0]["unique_identifier"] == SENSOR_ID1
    assert weather_sensors[0]["sensor_type_name"] == "weather"
    assert weather_sensors[1]["unique_identifier"] == SENSOR_ID2
    assert weather_sensors[1]["sensor_type_name"] == "weather"


def test_list_sensor_measures(session: Session) -> None:
    """Find the inserted sensor measures."""
    insert_measures(session)
    all_measures = sensors.list_sensor_measures(session=session)
    expected_keys = {"id", "name", "units", "datatype"}
    assert len(all_measures) == 2
    assert all_measures[0]["name"] == "temperature"
    assert set(all_measures[0].keys()) == expected_keys
    assert all_measures[1]["name"] == "is raining"


def test_list_sensor_types(session: Session) -> None:
    """Find the inserted sensor types."""
    insert_types(session)
    all_types = sensors.list_sensor_types(session=session)
    expected_keys = {"id", "name", "description", "measures"}
    assert len(all_types) == 2
    assert all_types[0]["name"] == "weather"
    assert {"name": "temperature", "units": "Kelvin", "datatype": "float"} in all_types[
        0
    ]["measures"]
    assert set(all_types[0].keys()) == expected_keys
    assert all_types[1]["name"] == "temperature"


def test_delete_sensor_measure(session: Session) -> None:
    """Delete a sensor measure, and check that it is deleted and can't be redeleted."""
    insert_measures(session)
    sensors.delete_sensor_measure("temperature", session=session)
    all_measures = sensors.list_sensor_measures(session=session)
    assert len(all_measures) == 1

    # Doing the same deletion again should fail, since that row is gone.
    error_msg = "No sensor measure named 'temperature'"
    with pytest.raises(ValueError, match=error_msg):
        sensors.delete_sensor_measure("temperature", session=session)


def test_delete_sensor_measure_type_exists(session: Session) -> None:
    """Try to delete a sensor measure for which a sensor type exists."""
    insert_types(session)
    error_msg = (
        'update or delete on table "sensor_measure" violates foreign key constraint '
        '"sensor_type_measure_relation_measure_id_fkey" on table '
        '"sensor_type_measure_relation"'
    )
    with pytest.raises(IntegrityError, match=error_msg):
        sensors.delete_sensor_measure("temperature", session=session)


def test_delete_sensor_type(session: Session) -> None:
    """Delete a sensor type, and check that it is deleted and can't be redeleted."""
    insert_types(session)
    sensors.delete_sensor_type("weather", session=session)
    all_types = sensors.list_sensor_types(session=session)
    assert len(all_types) == 1

    # Doing the same deletion again should fail, since that row is gone.
    error_msg = "No sensor type named 'weather'"
    with pytest.raises(ValueError, match=error_msg):
        sensors.delete_sensor_type("weather", session=session)


def test_delete_sensor_type_sensor_exists(session: Session) -> None:
    """Try to delete a sensor type for which a sensor exists."""
    insert_sensors(session)
    error_msg = (
        'update or delete on table "sensor_type" violates foreign key '
        'constraint "sensor_type_id_fkey" on table "sensor"'
    )
    with pytest.raises(IntegrityError, match=error_msg):
        sensors.delete_sensor_type("weather", session=session)


def test_delete_sensor(session: Session) -> None:
    """Delete a sensor, and check that it is deleted and can't be redeleted."""
    insert_sensors(session)
    sensors.delete_sensor(SENSOR_ID1, session=session)
    all_sensors = sensors.list_sensors(session=session)
    assert len(all_sensors) == 2

    # Doing the same deletion again should fail, since that row is gone.
    error_msg = f"No sensor '{SENSOR_ID1}'"
    with pytest.raises(ValueError, match=error_msg):
        sensors.delete_sensor(SENSOR_ID1, session=session)


def test_delete_sensor_nonexistent(session: Session) -> None:
    """Try to delete a non-existent sensor."""
    insert_sensors(session)
    error_msg = "No sensor 'BLAHBLAH'"
    with pytest.raises(ValueError, match=error_msg):
        sensors.delete_sensor("BLAHBLAH", session=session)


def test_edit_sensor(session: Session) -> None:
    """Edit a sensor, and check that it is edited."""
    insert_sensors(session)
    sensors.edit_sensor(
        SENSOR_ID1, new_name="new_name", new_notes="new_notes", session=session
    )
    session.commit()
    all_sensors = sensors.list_sensors(session=session)
    assert len(all_sensors) == 3

    for sensor in all_sensors:
        if sensor.get("unique_identifier") == SENSOR_ID1:
            assert sensor.get("name") == "new_name"
            assert sensor.get("notes") == "new_notes"
