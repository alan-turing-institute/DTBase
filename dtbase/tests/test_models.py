"""
Test the functions for accessing the model tables.
"""
import datetime as dt

import sqlalchemy as sqla
import pytest

from dtbase.core import models

# We use this in many places, and I don't want to type out the whole thing every time.
NOW = dt.datetime.now()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Functions for inserting some data into the database. These will called at the
# beginning of many tests to populate the database with data to test against. They are a
# lot like fixtures, but aren't fixtures because running them successfully is a test in
# itself.

MODEL_NAME1 = "Murphy's Law"
MODEL_NAME2 = "My Fortune Teller Says So"
SCENARIO1 = "The absolute worst case scenario"
SCENARIO2 = "The really-bad-but-could-actually-technically-be-worse scenario"
SCENARIO3 = "Use only a single deck of tarot cards."
MEASURE_NAME1 = "mean temperature"
MEASURE_UNITS1 = "Kelvin"
MEASURE_NAME2 = "likely to rain"
MEASURE_UNITS2 = ""


def insert_models(session):
    """Insert some models into the database."""
    models.insert_model(name=MODEL_NAME1, session=session)
    models.insert_model(name=MODEL_NAME2, session=session)


def insert_scenarios(session):
    """Insert model scenarios into the database."""
    insert_models(session)
    models.insert_model_scenario(
        model_name=MODEL_NAME1,
        description=SCENARIO1,
        session=session,
    )
    models.insert_model_scenario(
        model_name=MODEL_NAME1,
        description=SCENARIO2,
        session=session,
    )
    models.insert_model_scenario(
        model_name=MODEL_NAME2,
        description=SCENARIO3,
        session=session,
    )


def insert_measures(session):
    """Insert some model measures into the database."""
    models.insert_model_measure(
        name=MEASURE_NAME1, units=MEASURE_UNITS1, datatype="float", session=session
    )
    models.insert_model_measure(
        name=MEASURE_NAME2, units=MEASURE_UNITS2, datatype="boolean", session=session
    )


def insert_runs(session, time_created=NOW):
    """Insert some model runs into the database."""
    insert_scenarios(session)
    insert_measures(session)
    product1 = {
        "measure_name": MEASURE_NAME2,
        "values": [True, True, True],
        "timestamps": [
            NOW + dt.timedelta(days=1),
            NOW + dt.timedelta(days=2),
            NOW + dt.timedelta(days=3),
        ],
    }
    product2 = {
        "measure_name": MEASURE_NAME1,
        "values": [-23.0, -23.0, -23.1],
        "timestamps": [
            NOW + dt.timedelta(days=1),
            NOW + dt.timedelta(days=2),
            NOW + dt.timedelta(days=3),
        ],
    }
    product3 = {
        "measure_name": MEASURE_NAME2,
        "values": [False, True, False],
        "timestamps": [
            NOW + dt.timedelta(months=1),
            NOW + dt.timedelta(months=2),
            NOW + dt.timedelta(months=3),
        ],
    }
    models.insert_model_run(
        model_name=MODEL_NAME1,
        scenario_description=SCENARIO1,
        measures_and_values=[product1, product2],
        time_created=time_created,
        session=session,
    )
    models.insert_model_run(
        model_name=MODEL_NAME2,
        scenario_description=SCENARIO3,
        measures_and_values=[product3],
        time_created=time_created,
        session=session,
    )


def test_list_model_measures(session):
    """Find the inserted model measures."""
    insert_measures(session)
    all_measures = models.list_model_measures(session=session)
    expected_keys = {"id", "name", "units", "datatype"}
    assert len(all_measures) == 2
    assert all_measures[0]["name"] == "temperature"
    assert set(all_measures[0].keys()) == expected_keys
    assert all_measures[1]["name"] == "is raining"


def test_delete_model_measure(session):
    """Delete a model measure, and check that it is deleted and can't be redeleted."""
    insert_measures(session)
    models.delete_model_measure("temperature", session=session)
    all_measures = models.list_model_measures(session=session)
    assert len(all_measures) == 1

    # Doing the same deletion again should fail, since that row is gone.
    error_msg = "No model measure named 'temperature'"
    with pytest.raises(ValueError, match=error_msg):
        models.delete_model_measure("temperature", session=session)


def test_delete_model_measure_type_exists(session):
    """Try to delete a model measure for which a model type exists."""
    insert_types(session)
    error_msg = (
        'update or delete on table "model_measure" violates foreign key constraint '
        '"model_type_measure_relation_measure_id_fkey" on table '
        '"model_type_measure_relation"'
    )
    with pytest.raises(sqla.exc.IntegrityError, match=error_msg):
        models.delete_model_measure("temperature", session=session)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Tests for models


def test_insert_model(session):
    """Test inserting models."""
    insert_models(session)


def test_insert_model_duplicate(session):
    """Try to insert a model that already exists."""
    insert_models(session)
    error_msg = 'duplicate key value violates unique constraint "model_name_key"'
    with pytest.raises(sqla.exc.IntegrityError, match=error_msg):
        models.insert_model(MODEL_NAME1, session=session)


def test_list_models(session):
    """Find the inserted models."""
    insert_models(session)
    all_models = models.list_models(session=session)
    expected_keys = {"id", "name"}
    assert len(all_models) == 2
    assert set(all_models[0].keys()) == expected_keys
    assert all_models[0]["name"] == MODEL_NAME1
    assert all_models[1]["name"] == MODEL_NAME2


def test_delete_model(session):
    """Delete a model, and check that it is deleted and can't be redeleted."""
    insert_models(session)
    models.delete_model(MODEL_NAME1, session=session)
    all_models = models.list_models(session=session)
    assert len(all_models) == 1

    # Doing the same deletion again should fail, since that row is gone.
    error_msg = f"No model named '{MODEL_NAME1}'"
    with pytest.raises(ValueError, match=error_msg):
        models.delete_model(MODEL_NAME1, session=session)


def test_delete_model_nonexistent(session):
    """Try to delete a non-existent model."""
    insert_models(session)
    error_msg = "No model named 'BLAHBLAH'"
    with pytest.raises(ValueError, match=error_msg):
        models.delete_model("BLAHBLAH", session=session)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Tests for model scenarios


def test_insert_model_scenarios(session):
    """Test inserting a model scenario."""
    insert_scenarios(session)


def test_insert_model_scenarios_duplicate(session):
    """Try to insert a model scenario that conflicts with one that exists."""
    insert_scenarios(session)
    error_msg = (
        "duplicate key value violates unique constraint "
        '"model_scenario_model_id_description_key"'
    )
    with pytest.raises(sqla.exc.IntegrityError, match=error_msg):
        models.insert_model_scenario(
            model_name=MODEL_NAME1, description=SCENARIO1, session=session
        )


def test_insert_model_scenarios_no_model(session):
    """Try to insert a model scenario that uses measures that don't exist."""
    insert_scenarios(session)
    error_msg = "No model named 'Flip A Coin'"
    with pytest.raises(ValueError, match=error_msg):
        models.insert_model_scenario(
            model_name="Flip A Coin", description="A fair coin", session=session
        )


def test_list_model_scenarios(session):
    """Find the inserted model scenarios."""
    insert_scenarios(session)
    all_scenarios = models.list_model_scenarios(session=session)
    expected_keys = {"id", "model_id", "description"}
    assert len(all_scenarios) == 2
    assert all_scenarios[0]["name"] == "weather"
    assert {
        "name": "temperature",
        "units": "Kelvin",
        "datascenario": "float",
    } in all_scenarios[0]["measures"]
    assert set(all_scenarios[0].keys()) == expected_keys
    assert all_scenarios[1]["name"] == "temperature"


def test_delete_model_scenario(session):
    """Delete a model scenario, and check that it is deleted and can't be redeleted."""
    insert_scenarios(session)
    models.delete_model_scenario("weather", session=session)
    all_scenarios = models.list_model_scenarios(session=session)
    assert len(all_scenarios) == 1

    # Doing the same deletion again should fail, since that row is gone.
    error_msg = "No model scenario named 'weather'"
    with pytest.raises(ValueError, match=error_msg):
        models.delete_model_scenario("weather", session=session)


def test_delete_model_scenario_model_exists(session):
    """Try to delete a model scenario for which a model exists."""
    insert_models(session)
    error_msg = (
        'update or delete on table "model_scenario" violates foreign key '
        'constraint "model_scenario_id_fkey" on table "model"'
    )
    with pytest.raises(sqla.exc.IntegrityError, match=error_msg):
        models.delete_model_scenario("weather", session=session)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Tests for model measures


def test_insert_model_measure(session):
    """Test inserting model measures."""
    insert_measures(session)


def test_insert_model_measure_duplicate(session):
    """Try to insert a model measure that conflicts with one that exists."""
    insert_measures(session)
    # This is fine, because the units are different.
    models.insert_model_measure(
        name=MEASURE_NAME1, units="Celsius", datatype="float", session=session
    )
    # This is a duplicate.
    error_msg = (
        'duplicate key value violates unique constraint "model_measure_name_units_key"'
    )
    with pytest.raises(sqla.exc.IntegrityError, match=error_msg):
        models.insert_model_measure(
            name=MEASURE_NAME1, units="Kelvin", datatype="integer", session=session
        )


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Tests for model values


def test_insert_model_values(session):
    """Test inserting model values"""
    insert_values(session)
    read_values = models.get_model_values(
        "temperature",
        SENSOR_ID1,
        dt_from=TIMESTAMPS[0],
        dt_to=TIMESTAMPS[-1],
        session=session,
    )
    assert read_values == list(zip(TEMPERATURES, TIMESTAMPS))


def test_read_partial_model_values(session):
    """Test inserting model values"""
    insert_values(session)
    # Read all except first value.
    read_values = models.get_model_values(
        "temperature",
        SENSOR_ID1,
        dt_from=TIMESTAMPS[1],
        dt_to=TIMESTAMPS[-1],
        session=session,
    )
    assert read_values == list(zip(TEMPERATURES[1:], TIMESTAMPS[1:]))


def test_insert_model_values_wrong_measure(session):
    """Try to insert model values with the wrong measure."""
    insert_models(session)
    error_msg = (
        "Measure 'temperature misspelled' is not a valid measure for model "
        f"'{SENSOR_ID1}'."
    )
    with pytest.raises(ValueError, match=error_msg):
        models.insert_model_values(
            "temperature misspelled",
            SENSOR_ID1,
            TEMPERATURES,
            TIMESTAMPS,
            session=session,
        )


def test_insert_model_values_wrong_number(session):
    """Try to insert too few or too many model values."""
    insert_models(session)
    error_msg = (
        "There should be as many values as there are timestamps, but got 4 and 3"
    )
    with pytest.raises(ValueError, match=error_msg):
        models.insert_model_values(
            "temperature",
            SENSOR_ID1,
            TEMPERATURES + [23.0],
            TIMESTAMPS,
            session=session,
        )
    error_msg = (
        "There should be as many values as there are timestamps, but got 2 and 3"
    )
    with pytest.raises(ValueError, match=error_msg):
        models.insert_model_values(
            "temperature",
            SENSOR_ID1,
            TEMPERATURES[:-1],
            TIMESTAMPS,
            session=session,
        )


def test_insert_model_values_wrong_type(session):
    """Try to insert model values of the wrong type."""
    insert_models(session)
    error_msg = (
        "For model measure 'temperature' expected a values of type float "
        "but got a <class 'bool'>."
    )
    with pytest.raises(ValueError, match=error_msg):
        models.insert_model_values(
            "temperature",
            SENSOR_ID1,
            [True, False, False],
            TIMESTAMPS,
            session=session,
        )
    error_msg = (
        'column "timestamp" is of type timestamp without time zone but '
        "expression is of type boolean"
    )
    with pytest.raises(sqla.exc.ProgrammingError, match=error_msg):
        models.insert_model_values(
            "temperature",
            SENSOR_ID1,
            TEMPERATURES,
            [True, False, False],
            session=session,
        )


def test_insert_model_values_duplicate(session):
    """Try to insert model values of the wrong type."""
    insert_values(session)
    error_msg = (
        "duplicate key value violates unique constraint "
        '"model_float_value_measure_id_model_id_timestamp_key"'
    )
    with pytest.raises(sqla.exc.IntegrityError, match=error_msg):
        models.insert_model_values(
            "temperature",
            SENSOR_ID1,
            [23.0, 23.0, 23.0],
            TIMESTAMPS,
            session=session,
        )
