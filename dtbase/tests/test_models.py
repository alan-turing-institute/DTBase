"""
Test the functions for accessing the model tables.
"""
import datetime as dt

import sqlalchemy as sqla
import pytest

from dtbase.core import models

# We use this in many places, and I don't want to type out the whole thing every time.
NOW = dt.datetime.now(dt.timezone.utc)

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
PRODUCT1 = {
    "measure_name": MEASURE_NAME1,
    "values": [-23.0, -23.0, -23.1],
    "timestamps": [
        NOW + dt.timedelta(days=1),
        NOW + dt.timedelta(days=2),
        NOW + dt.timedelta(days=3),
    ],
}
PRODUCT2 = {
    "measure_name": MEASURE_NAME2,
    "values": [True, True, True],
    "timestamps": [
        NOW + dt.timedelta(days=1),
        NOW + dt.timedelta(days=2),
        NOW + dt.timedelta(days=3),
    ],
}
PRODUCT3 = {
    "measure_name": MEASURE_NAME2,
    "values": [False, True, False],
    "timestamps": [
        NOW + dt.timedelta(weeks=1),
        NOW + dt.timedelta(weeks=2),
        NOW + dt.timedelta(weeks=3),
    ],
}


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


def insert_runs(session):
    """Insert some model runs into the database."""
    insert_scenarios(session)
    insert_measures(session)
    models.insert_model_run(
        model_name=MODEL_NAME1,
        scenario_description=SCENARIO1,
        measures_and_values=[PRODUCT1, PRODUCT2],
        time_created=NOW,
        session=session,
    )
    models.insert_model_run(
        model_name=MODEL_NAME1,
        scenario_description=SCENARIO2,
        measures_and_values=[PRODUCT1, PRODUCT2],
        time_created=NOW + dt.timedelta(days=1),
        session=session,
    )
    models.insert_model_run(
        model_name=MODEL_NAME2,
        scenario_description=SCENARIO3,
        measures_and_values=[PRODUCT3],
        time_created=NOW,
        session=session,
    )


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
    assert len(all_scenarios) == 3
    assert set(all_scenarios[0].keys()) == expected_keys
    assert set(all_scenarios[1].keys()) == expected_keys
    assert all_scenarios[0]["description"] == SCENARIO1


def test_delete_model_scenario(session):
    """Delete a model scenario, and check that it is deleted and can't be redeleted."""
    insert_scenarios(session)
    models.delete_model_scenario(MODEL_NAME1, SCENARIO1, session=session)
    all_scenarios = models.list_model_scenarios(session=session)
    assert len(all_scenarios) == 2

    # Doing the same deletion again should fail, since that row is gone.
    error_msg = f"No model scenario '{SCENARIO1}' for model '{MODEL_NAME1}'"
    with pytest.raises(ValueError, match=error_msg):
        models.delete_model_scenario(MODEL_NAME1, SCENARIO1, session=session)


def test_delete_model_scenario_model_exists(session):
    """Try to delete a model scenario for which a model exists."""
    insert_models(session)
    error_msg = f"No model scenario '{SCENARIO1}' for model '{MODEL_NAME1}'"
    with pytest.raises(ValueError, match=error_msg):
        models.delete_model_scenario(MODEL_NAME1, SCENARIO1, session=session)


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


def test_list_model_measures(session):
    """Find the inserted model measures."""
    insert_measures(session)
    all_measures = models.list_model_measures(session=session)
    expected_keys = {"id", "name", "units", "datatype"}
    assert len(all_measures) == 2
    assert set(all_measures[0].keys()) == expected_keys
    assert set(all_measures[1].keys()) == expected_keys
    assert all_measures[0]["name"] == MEASURE_NAME1
    assert all_measures[1]["name"] == MEASURE_NAME2


def test_delete_model_measure(session):
    """Delete a model measure, and check that it is deleted and can't be redeleted."""
    insert_measures(session)
    models.delete_model_measure(MEASURE_NAME1, session=session)
    all_measures = models.list_model_measures(session=session)
    assert len(all_measures) == 1

    # Doing the same deletion again should fail, since that row is gone.
    error_msg = f"No model measure named '{MEASURE_NAME1}'"
    with pytest.raises(ValueError, match=error_msg):
        models.delete_model_measure(MEASURE_NAME1, session=session)


def test_delete_model_run_exists(session):
    """Try to delete a model measure for which a model run exists."""
    insert_runs(session)
    error_msg = (
        'update or delete on table "model" violates foreign key constraint '
        '"model_run_model_id_fkey" on table "model_run"'
    )
    with pytest.raises(sqla.exc.IntegrityError, match=error_msg):
        models.delete_model(MODEL_NAME1, session=session)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Tests for model runs


def test_insert_model_runs(session):
    """Test inserting model runs"""
    insert_runs(session)


def test_insert_model_runs_duplicate(session):
    """Try to insert a model run that already exists."""
    insert_runs(session)
    error_msg = (
        "duplicate key value violates unique constraint "
        '"model_run_model_id_scenario_id_time_created_key"'
    )
    with pytest.raises(sqla.exc.IntegrityError, match=error_msg):
        models.insert_model_run(
            model_name=MODEL_NAME1,
            scenario_description=SCENARIO1,
            measures_and_values=[PRODUCT1, PRODUCT2],
            time_created=NOW,
            session=session,
        )


def test_list_model_runs(session):
    """Test listing model runs."""
    insert_runs(session)
    # Get all runs for MODEL_NAME1
    runs = models.list_model_runs(MODEL_NAME1, session=session)
    expected_keys = {
        "id",
        "model_id",
        "model_name",
        "scenario_id",
        "scenario_description",
        "time_created",
    }
    assert len(runs) == 2
    for run in runs:
        assert set(run.keys()) == expected_keys

    # Similarly for MODEL_NAME2
    runs = models.list_model_runs(MODEL_NAME2, session=session)
    expected_keys = {
        "id",
        "model_id",
        "model_name",
        "scenario_id",
        "scenario_description",
        "time_created",
    }
    assert len(runs) == 1
    for run in runs:
        assert set(run.keys()) == expected_keys


def test_list_model_runs_by_scenario(session):
    """Test listing model runs."""
    insert_runs(session)
    runs = models.list_model_runs(MODEL_NAME1, scenario=SCENARIO1, session=session)
    expected_keys = {
        "id",
        "model_id",
        "model_name",
        "scenario_id",
        "scenario_description",
        "time_created",
    }
    assert len(runs) == 1
    for run in runs:
        assert set(run.keys()) == expected_keys


def test_list_model_runs_by_time(session):
    """Test listing model runs."""
    insert_runs(session)
    # Exclude one run using dt_from
    runs = models.list_model_runs(
        MODEL_NAME1, dt_from=NOW + dt.timedelta(hours=12), session=session
    )
    expected_keys = {
        "id",
        "model_id",
        "model_name",
        "scenario_id",
        "scenario_description",
        "time_created",
    }
    assert len(runs) == 1
    for run in runs:
        assert set(run.keys()) == expected_keys

    # Exclude one run using dt_to
    runs = models.list_model_runs(
        MODEL_NAME1, dt_to=NOW + dt.timedelta(hours=12), session=session
    )
    expected_keys = {
        "id",
        "model_id",
        "model_name",
        "scenario_id",
        "scenario_description",
        "time_created",
    }
    assert len(runs) == 1
    for run in runs:
        assert set(run.keys()) == expected_keys


def test_get_model_run(session):
    """Test getting the results of a model run."""
    insert_runs(session)
    # Find the ID of one of the runs
    runs = models.list_model_runs(
        MODEL_NAME1, dt_to=NOW + dt.timedelta(hours=12), session=session
    )
    run_id = next(r["id"] for r in runs if r["scenario_description"] == SCENARIO1)
    # Get the run
    #values = models.get_model_run(run_id, MEASURE_NAME1, session=session)
    values = models.get_model_run_results_for_measure(run_id, MEASURE_NAME1, session=session)
    assert values == list(zip(PRODUCT1["values"], PRODUCT1["timestamps"]))


def test_insert_model_run_no_scenario(session):
    """Try to insert model values with the wrong measure."""
    insert_scenarios(session)
    insert_measures(session)
    scenario_description = "A best case scenario"
    error_msg = f"No model scenario '{scenario_description}' for model '{MODEL_NAME1}'."
    with pytest.raises(ValueError, match=error_msg):
        models.insert_model_run(
            model_name=MODEL_NAME1,
            scenario_description=scenario_description,
            measures_and_values=[PRODUCT1, PRODUCT2],
            time_created=NOW,
            session=session,
        )
    # The above fails because the scenario doesn't exist, but the below passes because
    # we instruct insert_model_run to create the scenario if necessary.
    models.insert_model_run(
        model_name=MODEL_NAME1,
        scenario_description=scenario_description,
        measures_and_values=[PRODUCT1, PRODUCT2],
        time_created=NOW,
        create_scenario=True,
        session=session,
    )

    scenarios = models.list_model_scenarios(session=session)
    assert any(s["description"] == scenario_description for s in scenarios)


def test_insert_model_run_wrong_number(session):
    """Try to insert too few or too many model values."""
    insert_scenarios(session)
    insert_measures(session)
    product = {
        "measure_name": MEASURE_NAME1,
        "values": [-23.0, -23.0],
        "timestamps": [
            NOW + dt.timedelta(days=1),
            NOW + dt.timedelta(days=2),
            NOW + dt.timedelta(days=3),
        ],
    }
    error_msg = (
        "There should be as many values as there are timestamps, but got 2 and 3"
    )
    with pytest.raises(ValueError, match=error_msg):
        models.insert_model_run(
            model_name=MODEL_NAME1,
            scenario_description=SCENARIO1,
            measures_and_values=[PRODUCT1, product],
            time_created=NOW,
            session=session,
        )


def test_insert_model_run_wrong_type(session):
    """Try to insert model values of the wrong type."""
    insert_scenarios(session)
    insert_measures(session)
    product = {
        "measure_name": MEASURE_NAME1,
        "values": ["dada", "is", "king"],
        "timestamps": [
            NOW + dt.timedelta(days=1),
            NOW + dt.timedelta(days=2),
            NOW + dt.timedelta(days=3),
        ],
    }
    error_msg = (
        f"For model measure '{MEASURE_NAME1}' expected values of type float "
        "but got <class 'str'>."
    )
    with pytest.raises(ValueError, match=error_msg):
        models.insert_model_run(
            model_name=MODEL_NAME1,
            scenario_description=SCENARIO1,
            measures_and_values=[PRODUCT1, product],
            time_created=NOW,
            session=session,
        )
