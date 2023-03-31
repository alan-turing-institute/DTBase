"""Functions for accessing the sensor tables. """
import sqlalchemy as sqla

from dtbase.backend.utils import add_default_session
from dtbase.core import queries
from dtbase.core.structure import (
    Sensor,
    SensorMeasure,
    SensorType,
    SensorTypeMeasureRelation,
)
from dtbase.core import utils


@add_default_session
def measure_id_from_name(measure_name, session=None):
    """Find the id of a sensor measure of the given name.

    Args:
        measure_name: Name of the sensor measure
        session: SQLAlchemy session. Optional.

    Returns:
        Database id of the sensor measure.
    """
    query = sqla.select(SensorMeasure.id).where(SensorMeasure.name == measure_name)
    result = session.execute(query).fetchall()
    if len(result) == 0:
        raise ValueError(f"No sensor measure named '{measure_name}'")
    if len(result) > 1:
        raise ValueError(f"Multiple sensor measures named '{measure_name}'")
    return result[0][0]


@add_default_session
def type_id_from_name(type_name, session=None):
    """Find the id of a sensor type of the given name.

    Args:
        type_name: Name of the sensor type
        session: SQLAlchemy session. Optional.

    Returns:
        Database id of the sensor type.
    """
    query = sqla.select(SensorType.id).where(SensorType.name == type_name)
    result = session.execute(query).fetchall()
    if len(result) == 0:
        raise ValueError(f"No sensor type named '{type_name}'")
    if len(result) > 1:
        raise ValueError(f"Multiple sensor types named '{type_name}'")
    return result[0][0]


@add_default_session
def sensor_id_from_unique_identifier(unique_identifier, session=None):
    """Find the id of a sensor of the given unique identifier.

    Args:
        unique_identifier: Unique identifier of the sensor.
        session: SQLAlchemy session. Optional.

    Returns:
        Database id of the sensor.
    """
    query = sqla.select(Sensor.id).where(Sensor.unique_identifier == unique_identifier)
    result = session.execute(query).fetchall()
    if len(result) == 0:
        raise ValueError(f"No sensor '{unique_identifier}'")
    if len(result) > 1:
        raise ValueError(f"Multiple sensors '{unique_identifier}'")
    return result[0][0]


@add_default_session
def insert_sensor_measure(name, units, datatype, session=None):
    """Insert a new sensor measure into the database.

    Sensor measures are types of readings that sensors can report. For instance
    "temperature", "electricity consumption", or "air flow".

    Args:
        name: Name of this measure, e.g. "temperature".
        units: Units in which this measure is specified.
        datatype: Value type of this sensor measure. Has to be one of "string",
            "integer", "float", or "boolean".
        session: SQLAlchemy session. Optional.

    Returns:
        None
    """
    if datatype not in ("string", "integer", "float", "boolean"):
        raise ValueError(f"Unrecognised data type: {datatype}")
    session.add(SensorMeasure(name=name, units=units, datatype=datatype))
    session.flush()


@add_default_session
def insert_sensor_type(name, description, measures, session=None):
    """Insert a new sensor type into the database.

    Sensor type specifies a set of measures that sensors of this type can report. For
    instance, an atmospheric sensor might report temperature and air pressure. Sensor
    types can also have a name and a free form description.

    Args:
        name: Name of this sensor type
        description: Free form text description, for human consumption.
        measures: List of sensor measures that this sensor type can report.
            This should be a list of strings, that are the names of existing measures
            in the database.
        session: SQLAlchemy session. Optional.

    Returns:
        None
    """
    new_type = SensorType(name=name, description=description)
    session.add(new_type)
    session.flush()
    for measure_name in measures:
        measure_id = measure_id_from_name(measure_name, session=session)
        session.add(
            SensorTypeMeasureRelation(type_id=new_type.id, measure_id=measure_id)
        )
    session.flush()


@add_default_session
def insert_sensor(type_name, unique_identifier, name=None, notes=None, session=None):
    """Insert a new sensor into the database.

    Args:
        type_name: Name of the sensor type that this sensor is of.
        unique_identifier: A unique string that singles out this sensor.
        name: A human-readable name for this sensor. Optional.
        notes: Free-form text notes to attach to this sensor. Optional.
        session: SQLAlchemy session. Optional.

    Returns:
        None
    """
    type_id = type_id_from_name(type_name, session=session)
    new_sensor = Sensor(
        type_id=type_id, unique_identifier=unique_identifier, name=name, notes=notes
    )
    session.add(new_sensor)
    session.flush()


@add_default_session
def insert_sensor_readings(
    measure_name, sensor_uniq_id, readings, timestamps, session=None
):
    """Insert sensor readings to the database.

    Args:
        measure_name: Name of the sensor measure that these are readings for.
        sensor_uniq_id: Unique identifier for the sensor that reports these readings.
        readings: Readings to insert. An iterable.
        timestamps: Timestamps associated with the readings. An iterable of the same
            length as readings.
        session: SQLAlchemy session. Optional.

    Returns:
        None
    """
    if len(readings) != len(timestamps):
        raise ValueError(
            "There should be as many readings as there are timestamps,"
            f" but got {len(readings)} and {len(timestamps)}"
        )
    if len(readings) == 0:
        return None

    # Check the type of readings to insert.
    example_element = readings[0]
    element_type = type(example_element)
    if element_type not in utils.sensor_reading_class_dict:
        msg = f"Don't know how to insert sensor readings of type {element_type}."
        raise ValueError(msg)
    readings_class = utils.sensor_reading_class_dict[element_type]

    # Check that this is a valid measure for the given sensor_type.
    measures_sq = queries.sensor_measures_by_type().subquery()
    measures_q = (
        sqla.select(
            measures_sq.c.measure_datatype,
        )
        .where(measures_sq.c.measure_name == measure_name)
        .join(Sensor, Sensor.type_id == measures_sq.c.type_id)
        .where(Sensor.unique_identifier == sensor_uniq_id)
    )
    measures_result = session.execute(measures_q).fetchall()
    valid_measure = len(measures_result) > 0
    if not valid_measure:
        raise ValueError(
            f"Measure '{measure_name}' is not a valid measure for sensor "
            f"'{sensor_uniq_id}'."
        )
    expected_datatype = measures_result[0][0]

    # Check that the data type is correct
    datatype_matches = utils.check_datatype(example_element, expected_datatype)
    if not datatype_matches:
        raise ValueError(
            f"For sensor measure '{measure_name}' expected readings of type "
            f"{expected_datatype} but got a {element_type}."
        )

    # All seems well, insert the values.
    # We use SQLAlchemy Core rather than ORM for performance reasons:
    # https://docs.sqlalchemy.org/en/14/faq/performance.html#i-m-inserting-400-000-rows-with-the-orm-and-it-s-really-slow
    measure_id = measure_id_from_name(measure_name, session=session)
    sensor_id = sensor_id_from_unique_identifier(sensor_uniq_id, session=session)
    rows = [
        {
            "value": value,
            "timestamp": timestamp,
            "sensor_id": sensor_id,
            "measure_id": measure_id,
        }
        for value, timestamp in zip(readings, timestamps)
    ]
    session.execute(readings_class.__table__.insert(), rows)
    session.flush()


@add_default_session
def get_datatype_by_measure_name(measure_name, session=None):
    """Get the datatype of the sensor measure named.

    Args:
        measure_name: Name of the sensor measure.
        session: SQLAlchemy session. Optional.

    Return:
        Name of the datatype, as a string.
    """
    query = sqla.select(SensorMeasure.datatype).where(
        SensorMeasure.name == measure_name
    )
    result = session.execute(query).fetchall()
    if len(result) == 0:
        raise ValueError(f"No sensor measure named '{measure_name}'")
    datatype = result[0][0]
    return datatype


@add_default_session
def get_sensor_readings(measure_name, sensor_uniq_id, dt_from, dt_to, session=None):
    """Get sensor readings from the database.

    Args:
        measure_name: Name of the sensor measure to get readings for.
        sensor_uniq_id: Unique identifier for the sensor to get readings for.
        dt_from: Datetime object for earliest readings to get. Inclusive.
        dt_to: Datetime object for last readings to get. Inclusive.
        session: SQLAlchemy session. Optional.

    Returns:
        Readings from the database.
    """
    datatype_name = get_datatype_by_measure_name(measure_name, session=session)
    value_class = utils.sensor_reading_class_dict[datatype_name]
    query = (
        sqla.select(value_class.value, value_class.timestamp)
        .join(Sensor, Sensor.id == value_class.sensor_id)
        .join(SensorMeasure, SensorMeasure.id == value_class.measure_id)
        .where(
            (Sensor.unique_identifier == sensor_uniq_id)
            & (SensorMeasure.name == measure_name)
            & (value_class.timestamp >= dt_from)
            & (value_class.timestamp <= dt_to)
        )
    )
    result = session.execute(query).fetchall()
    return result


@add_default_session
def delete_sensor(unique_identifier, session=None):
    """Delete a sensor from the database.

    Also deletes any readings for this sensor.

    Args:
        unique_identifier: Unique identifier by which the sensor is recognised.
        session: SQLAlchemy session. Optional.

    Returns:
        None
    """
    result = session.execute(
        sqla.delete(Sensor).where(Sensor.unique_identifier == unique_identifier)
    )
    if result.rowcount == 0:
        raise ValueError(f"No sensor '{unique_identifier}'")


@add_default_session
def delete_sensor_measure(measure_name, session=None):
    """Delete a sensor measure from the database.

    Refuses to proceed if there are sensor readings or sensor types attached to this
    measure.

    Args:
        measure_name: Name of the measure to delete.
        session: SQLAlchemy session. Optional.

    Returns:
        None
    """
    result = session.execute(
        sqla.delete(SensorMeasure).where(SensorMeasure.name == measure_name)
    )
    if result.rowcount == 0:
        raise ValueError(f"No sensor measure named '{measure_name}'")


@add_default_session
def delete_sensor_type(type_name, session=None):
    """Delete a sensor type from the database.

    Refuses to proceed if there are sensors of this type in the database.

    Args:
        type_name: Name of the measure to delete.
        session: SQLAlchemy session. Optional.

    Returns:
        None
    """
    result = session.execute(
        sqla.delete(SensorType).where(SensorType.name == type_name)
    )
    if result.rowcount == 0:
        raise ValueError(f"No sensor type named '{type_name}'")


@add_default_session
def list_sensor_measures(session=None):
    """List all sensor measures.

    Args:
        session: SQLAlchemy session. Optional.

    Returns:
        List of all sensor measures.
    """
    query = sqla.select(
        SensorMeasure.id,
        SensorMeasure.name,
        SensorMeasure.units,
        SensorMeasure.datatype,
    )
    result = session.execute(query).mappings().all()
    result = utils.row_mappings_to_dicts(result)
    return result


@add_default_session
def list_sensor_types(session=None):
    """List all sensor types.

    Args:
        session: SQLAlchemy session. Optional.

    Returns:
        List of all sensor types.
    """
    measures_query = queries.sensor_measures_by_type()
    all_measures = session.execute(measures_query).mappings().all()
    types_query = sqla.select(SensorType.id, SensorType.name, SensorType.description)
    result = session.execute(types_query).mappings().all()
    result = utils.row_mappings_to_dicts(result)
    # To each sensor type, attach a list of measures
    for row in result:
        type_name = row["name"]
        measures = []
        for measure in all_measures:
            if measure["type_name"] == type_name:
                measures.append(
                    {
                        "name": measure["measure_name"],
                        "units": measure["measure_units"],
                        "datatype": measure["measure_datatype"],
                    }
                )
        row["measures"] = measures
    return result


@add_default_session
def list_sensors(type_name=None, session=None):
    """List all sensors, optionally filtering by sensor type.

    Args:
        type_name: Name of the sensor type to list instances of. Optional, by default
            list all sensors.
        session: SQLAlchemy session. Optional.

    Returns:
        List of all the sensors that match the provided criteria.
    """
    query = sqla.select(
        Sensor.id,
        Sensor.type_id.label("sensor_type_id"),
        Sensor.unique_identifier,
        Sensor.name,
        Sensor.notes,
        SensorType.name.label("sensor_type_name"),
    ).where(Sensor.type_id == SensorType.id)
    if type_name is not None:
        query = query.where(SensorType.name == type_name)
    result = session.execute(query).mappings().all()
    result = utils.row_mappings_to_dicts(result)
    return result
