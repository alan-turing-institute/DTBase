"""Functions for accessing the model tables."""
import datetime as dt
from typing import Any, List, Optional, Tuple

import sqlalchemy as sqla
from sqlalchemy.orm import Session

from dtbase.backend.utils import add_default_session
from dtbase.core import utils
from dtbase.core.structure import (
    Model,
    ModelMeasure,
    ModelProduct,
    ModelRun,
    ModelScenario,
    Sensor,
    SensorMeasure,
)


@add_default_session
def scenario_id_from_description(
    model_name: str, description: str, session: Optional[Session] = None
) -> None:
    """Find the id of a model scenario of the given description and model.

    Args:
        model_name: Name of the model for which this is a scenario.
        description: String description of the model scenario.
        session: SQLAlchemy session. Optional.

    Returns:
        Database id of the model scenario.
    """
    query = (
        sqla.select(ModelScenario.id)
        .join(Model, Model.id == ModelScenario.model_id)
        .where((Model.name == model_name) & (ModelScenario.description == description))
    )
    result = session.execute(query).fetchall()
    if len(result) == 0:
        raise ValueError(f"No model scenario '{description}' for model '{model_name}'.")
    return result[0][0]


@add_default_session
def measure_id_from_name(name: str, session: Optional[Session] = None) -> Any:
    """Find the id of a model measure of the given name.

    Args:
        name: Name of the model measure.
        session: SQLAlchemy session. Optional.

    Returns:
        Database id of the model measure.
    """
    query = sqla.select(ModelMeasure.id).where(ModelMeasure.name == name)
    result = session.execute(query).fetchall()
    if len(result) == 0:
        raise ValueError(f"No model measure '{name}'.")
    return result[0][0]


@add_default_session
def measure_name_from_id(measure_id: int, session: Optional[Session] = None) -> Any:
    """Find the name of a model measure given the id

    Args:
        measure_id:int ID of the model measure.
        session: SQLAlchemy session. Optional.

    Returns:
        Name of the model measure.
    """
    query = sqla.select(ModelMeasure.name).where(ModelMeasure.id == measure_id)
    result = session.execute(query).fetchall()
    if len(result) == 0:
        raise ValueError(f"No model measure '{measure_id}'.")
    return result[0][0]


@add_default_session
def model_id_from_name(name: str, session: Optional[Session] = None) -> Any:
    """Find the id of a model of the given name.

    Args:
        name: Name of the model.
        session: SQLAlchemy session. Optional.

    Returns:
        Database id of the model.
    """
    query = sqla.select(Model.id).where(Model.name == name)
    result = session.execute(query).fetchall()
    if len(result) == 0:
        raise ValueError(f"No model named '{name}'")
    return result[0][0]


@add_default_session
def insert_model(name: str, session: Optional[Session] = None) -> Model:
    """Insert a new model into the database.

    Args:
        name: Name of the model.
        session: SQLAlchemy session. Optional.

    Returns:
        The new Model
    """
    new_model = Model(name=name)
    session.add(new_model)
    session.flush()
    return new_model


@add_default_session
def insert_model_scenario(
    model_name: str, description: str, session: Optional[Session] = None
) -> ModelScenario:
    """Insert a new model scenario into the database.

    A model scenario specifies parameters for running a model. It is always tied to a
    particular model. It comes with a free form text description only (can also be
    null).

    Args:
        model_name: Name of this model type
        description: Free form text description. Can also be None/null.
        session: SQLAlchemy session. Optional.

    Returns:
        The new ModelScenario
    """
    model_id = model_id_from_name(model_name, session=session)
    new_scenario = ModelScenario(model_id=model_id, description=description)
    session.add(new_scenario)
    session.flush()
    return new_scenario


@add_default_session
def insert_model_measure(
    name: str,
    units: str,
    datatype: bool | str | int | float,
    session: Optional[Session] = None,
) -> ModelMeasure:
    """Insert a new model measure into the database.

    Model measures are types of values that models can output in their forecasts. For
    instance "mean temperature" or "upper bound for electricity consumption".

    Args:
        name: Name of this measure, e.g. "mean temperature".
        units: Units in which this measure is specified.
        datatype: Value type of this model measure. Has to be one of "string",
            "integer", "float", or "boolean".
        session: SQLAlchemy session. Optional.

    Returns:
        The new ModelMeasure
    """
    if datatype not in ("string", "integer", "float", "boolean"):
        raise ValueError(f"Unrecognised data type: {datatype}")
    new_measure = ModelMeasure(name=name, units=units, datatype=datatype)
    session.add(new_measure)
    session.flush()
    return new_measure


@add_default_session
def insert_model_product(
    model_run: ModelRun,
    measure_name: str,
    values: str,
    timestamps: dt.datetime,
    session: Optional[Session] = None,
) -> None:
    """Insert a model product and its results.

    Args:
        model_run: The ModelRun object for which this is a model product.
        measure_name: Name of the measure reported.
        values: Values that the model outputs as an iterable.
        timestamps: Timestamps associated with the values, an iterable of the same
            length.
        session: SQLAlchemy session. Optional.

    Returns:
        None
    """

    if len(values) != len(timestamps):
        raise ValueError(
            "There should be as many values as there are timestamps,"
            f" but got {len(values)} and {len(timestamps)}"
        )

    # Check the type of values to insert.
    example_element = values[0]
    element_type = type(example_element)
    if element_type not in utils.model_value_class_dict:
        msg = f"Don't know how to insert model values of type {element_type}."
        raise ValueError(msg)
    values_class = utils.model_value_class_dict[element_type]

    measure_query = sqla.select(ModelMeasure.datatype).where(
        ModelMeasure.name == measure_name
    )
    measure_result = session.execute(measure_query).fetchall()
    if measure_result is None:
        msg = f"Unknown model measure '{measure_name}'"
        raise ValueError(msg)
    if len(measure_result) > 1:
        msg = f"Multiple model measures called '{measure_name}'"
        raise ValueError(msg)
    expected_datatype = measure_result[0][0]

    # Check that the data type is correct
    datatype_matches = utils.check_datatype(example_element, expected_datatype)
    if not datatype_matches:
        raise ValueError(
            f"For model measure '{measure_name}' expected values of type "
            f"{expected_datatype} but got {element_type}."
        )

    # All seems well, insert the values.
    # We use SQLAlchemy Core rather than ORM for performance reasons:
    # https://docs.sqlalchemy.org/en/14/faq/performance.html#i-m-inserting-400-000-rows-with-the-orm-and-it-s-really-slow
    measure_id = measure_id_from_name(measure_name, session=session)
    model_product = ModelProduct(run_id=model_run.id, measure_id=measure_id)
    session.add(model_product)
    session.flush()
    product_id = model_product.id
    rows = [
        {
            "value": value,
            "timestamp": timestamp,
            "product_id": product_id,
        }
        for value, timestamp in zip(values, timestamps)
    ]
    session.execute(
        sqla.dialects.postgresql.insert(
            values_class.__table__
        ).on_conflict_do_nothing(),
        rows,
    )
    session.flush()


@add_default_session
def insert_model_run(
    model_name: str,
    scenario_description: str,
    measures_and_values: str,
    sensor_id: int = None,
    sensor_measure_id: int = None,
    time_created=dt.datetime.now(dt.timezone.utc),
    create_scenario: bool = False,
    session: Optional[Session] = None,
) -> None:
    """Insert a model run and its results.

    Args:
        model_name: Name of the model that was run.
        scenario_description: String that describes the scenario, i.e. how the model was
            run (values of parameters etc.)
        measures_and_values: Results of the model run. A list of dictionaries, each of
            which should have three values:
                measure_name: Name of the measure reported.
                values: Values that the model outputs as an iterable.
                timestamps: Timestamps associated with the values, an iterable of the
                    same length.
        sensor_id:int (optional) - database ID of sensor against which results should be
                     compared.
        sensor_measure_id: int (optional) - measure (e.g. "temperature") to compare to.
        time_created: Time when this run was run. Optional, `now` by default.
        create_scenario: Whether to create the scenario if it doesn't already exist.
            Optional, False by default.
        session: SQLAlchemy session. Optional.

    Returns:
        None
    """

    # Find/insert the scenario
    try:
        scenario_id = scenario_id_from_description(
            model_name, scenario_description, session=session
        )
    except ValueError:
        if create_scenario:
            scenario_id = insert_model_scenario(
                model_name, scenario_description, session=session
            ).id
        else:
            raise

    # Create the ModelRun
    model_id = model_id_from_name(model_name, session=session)
    model_run = ModelRun(
        model_id=model_id, scenario_id=scenario_id, time_created=time_created
    )
    if sensor_id:
        model_run.sensor_id = sensor_id
    if sensor_measure_id:
        model_run.sensor_measure_id = sensor_measure_id
    session.add(model_run)
    session.flush()
    for mnv in measures_and_values:
        measure_name = mnv["measure_name"]
        values = mnv["values"]
        timestamps = mnv["timestamps"]
        insert_model_product(
            model_run, measure_name, values, timestamps, session=session
        )
    return model_run.id


@add_default_session
def list_model_runs(
    model_name: str,
    dt_from: dt.datetime = None,
    dt_to: dt.datetime = None,
    scenario: str = None,
    session: Optional[Session] = None,
) -> List[dict]:
    """List model runs in a time window.

    Args:
        model_name: Name of the model to get runs for.
        dt_from: Datetime object for the earliest creation date for runs to include.
            Inclusive. Optional.
        dt_to: Datetime object for the last creation date for runs to include.
            Inclusive. Optional.
        scenario: The string description of the scenario to include runs for. Optional,
            by default all scenarios.
        session: SQLAlchemy session. Optional.

    Returns:
        List of model runs, each being a dict with keys:
         "id","model_id", "model_name", "scenario_id", "scenario_description",
         "time_created"
    """
    query = (
        sqla.select(
            ModelRun.id,
            ModelRun.model_id,
            Model.name.label("model_name"),
            ModelRun.scenario_id,
            ModelScenario.description.label("scenario_description"),
            ModelRun.time_created,
        )
        .join(Model, Model.id == ModelRun.model_id)
        .join(ModelScenario, ModelScenario.id == ModelRun.scenario_id)
        .where(Model.name == model_name)
    )
    if dt_from is not None:
        query = query.where(ModelRun.time_created >= dt_from)
    if dt_to is not None:
        query = query.where(ModelRun.time_created <= dt_to)
    if scenario is not None:
        query = query.where(ModelScenario.description == scenario)
    result = session.execute(query).mappings().all()
    result = utils.row_mappings_to_dicts(result)
    return result


@add_default_session
def get_datatype_by_measure_name(
    measure_name: str, session: Optional[Session] = None
) -> Any:
    """Get the datatype of the model measure named.

    Args:
        measure_name: Name of the model measure.
        session: SQLAlchemy session. Optional.

    Return:
        Name of the datatype, as a string.
    """
    query = sqla.select(ModelMeasure.datatype).where(ModelMeasure.name == measure_name)
    result = session.execute(query).fetchall()
    if len(result) == 0:
        raise ValueError("No model measure called '{measure_name}'")
    datatype = result[0][0]
    return datatype


@add_default_session
def get_model_run_results(run_id: int, session: Optional[Session] = None) -> Any:
    """Get the output of a model run for all measures.

    Args:
        run_id: Database ID of the model run.
        session: SQLAlchemy session. Optional.

    Returns:
        Dict {<measure_name>: list of tuples (values, timestamp), ...}

    """
    measures = get_model_run_measures(run_id, session=session)
    results = {}
    for (measure_name, measure_id) in measures:
        results[measure_name] = get_model_run_results_for_measure(
            run_id=run_id, measure_name=measure_name, session=session
        )
    return results


@add_default_session
def get_model_run_results_for_measure(
    run_id: int, measure_name: str = None, session: Optional[Session] = None
) -> Any:
    """Get the output of a model run for a single measure.

    Args:
        run_id: Database ID of the model run.
        measure_name: Name of the model measure to get values for. Optional.
        session: SQLAlchemy session. Optional.

    Returns:
        A list of tuples (values, timestamp) that are the results of the model run for
        that measure
    """

    datatype_name = get_datatype_by_measure_name(measure_name, session=session)
    value_class = utils.model_value_class_dict[datatype_name]
    measure_id = measure_id_from_name(measure_name, session=session)
    query = (
        sqla.select(value_class.value, value_class.timestamp)
        .join(ModelProduct, ModelProduct.id == value_class.product_id)
        .where(
            (ModelProduct.run_id == run_id) & (ModelProduct.measure_id == measure_id)
        )
    )
    result = session.execute(query).fetchall()
    return result


@add_default_session
def get_model_run_measures(
    run_id: int, session: Optional[Session] = None
) -> List[Tuple[str, int]]:
    """
    Get the list of ModelMeasures for a given ModelRun.

    Args:
        run_id:int Database ID of the model run
        session: SQLAlchemy session. Optional
    Returns:
        List of tuples [(<measure_name:str>, <measure_id:int>),...]
    """
    query = (
        sqla.select(ModelMeasure.name, ModelMeasure.id)
        .join(ModelProduct, ModelProduct.measure_id == ModelMeasure.id)
        .where((ModelProduct.run_id == run_id))
    )
    result = session.execute(query).fetchall()
    return result


@add_default_session
def get_model_run_sensor_measures(
    run_id: int, session: Optional[Session] = None
) -> Any:
    """
    Get the info about what sensor/measure can be compared to a given ModelRun.

    Args:
        run_id:int Database ID of the model run
        session: SQLAlchemy session. Optional
    Returns:
        tuple (<sensor_unique_id:str>, <measure_name:str>)
    """
    query = (
        sqla.select(ModelRun.sensor_id, Sensor.unique_identifier, SensorMeasure.name)
        .join(Sensor, Sensor.id == ModelRun.sensor_id)
        .join(SensorMeasure, SensorMeasure.id == ModelRun.sensor_measure_id)
        .where((ModelRun.id == run_id))
    )
    result = session.execute(query).fetchall()
    return result[0][1:]


@add_default_session
def delete_model(model_name: str, session: Optional[Session] = None) -> None:
    """Delete a model from the database.

    Refuses to proceed if there are runs for this model in the database.

    Args:
        model_name: Name of the model.
        session: SQLAlchemy session. Optional.

    Returns:
        None
    """
    result = session.execute(sqla.delete(Model).where(Model.name == model_name))
    if result.rowcount == 0:
        raise ValueError(f"No model named '{model_name}'.")


@add_default_session
def delete_model_scenario(
    model_name: str, description: str, session: Optional[Session] = None
) -> None:
    """Delete a model scenario from the database.

    Refuses to proceed if there are runs for this scenario in the database.

    Args:
        model_name: Name of the model for which this is a measure.
        description: Description of the measure to delete.
        session: SQLAlchemy session. Optional.

    Returns:
        None
    """
    model_id = model_id_from_name(model_name, session=session)
    result = session.execute(
        sqla.delete(ModelScenario).where(
            (ModelScenario.description == description)
            & (ModelScenario.model_id == model_id)
        )
    )
    if result.rowcount == 0:
        raise ValueError(f"No model scenario '{description}' for model '{model_name}'.")


@add_default_session
def delete_model_measure(name: str, session: Optional[Session] = None) -> None:
    """Delete a model measure from the database.

    Refuses to proceed if there are model products attached to this measure.

    Args:
        name: Name of the measure to delete.
        session: SQLAlchemy session. Optional.

    Returns:
        None
    """
    result = session.execute(sqla.delete(ModelMeasure).where(ModelMeasure.name == name))
    if result.rowcount == 0:
        raise ValueError(f"No model measure named '{name}'.")


@add_default_session
def delete_model_run(run_id: int, session: Optional[Session] = None) -> None:
    """Delete a model run from the database.

    Args:
        run_id: Database ID of the run to delete.
        session: SQLAlchemy session. Optional.

    Returns:
        None
    """
    result = session.execute(sqla.delete(ModelRun).where(ModelRun.id == run_id))
    if result.rowcount == 0:
        raise ValueError(f"No model run with ID {run_id}")


@add_default_session
def list_model_measures(session: Optional[Session] = None) -> List[dict]:
    """List all model measures.

    Args:
        session: SQLAlchemy session. Optional.

    Returns:
        List of all model measures.
    """
    query = sqla.select(
        ModelMeasure.id,
        ModelMeasure.name,
        ModelMeasure.units,
        ModelMeasure.datatype,
    )
    result = session.execute(query).mappings().all()
    result = utils.row_mappings_to_dicts(result)
    return result


@add_default_session
def list_model_scenarios(session: Optional[Session] = None) -> List[dict]:
    """List all model scenarios.

    Args:
        session: SQLAlchemy session. Optional.

    Returns:
        List of all model scenarios.
    """
    query = sqla.select(
        ModelScenario.id, ModelScenario.model_id, ModelScenario.description
    )
    result = session.execute(query).mappings().all()
    result = utils.row_mappings_to_dicts(result)
    return result


@add_default_session
def list_models(session: Optional[Session] = None) -> List[dict]:
    """List all models.

    Args:
        session: SQLAlchemy session. Optional.

    Returns:
        List of all models.
    """
    query = sqla.select(Model.id, Model.name)
    result = session.execute(query).mappings().all()
    result = utils.row_mappings_to_dicts(result)
    return result
