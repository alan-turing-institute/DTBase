"""Functions for accessing the sensor tables. """
import sqlalchemy as sqla

from dtbase.backend.utils import add_default_session
from dtbase.core import queries
from dtbase.core.structure import (
    Sensor,
    SensorBooleanReading,
    SensorFloatReading,
    SensorIntegerReading,
    SensorMeasure,
    SensorStringReading,
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
        raise ValueError(f"No sensor measure named {measure_name}")
    if len(result) > 1:
        raise ValueError(f"Multiple sensor measures named {measure_name}")
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
        raise ValueError(f"No sensor type named {type_name}")
    if len(result) > 1:
        raise ValueError(f"Multiple sensor types named {type_name}")
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
        raise ValueError(f"No sensor type {unique_identifier}")
    if len(result) > 1:
        raise ValueError(f"Multiple sensors {unique_identifier}")
    return result[0][0]


@add_default_session
def insert_sensor_measure(name, units, datatype, session=None):
    """Insert a new sensor measure into the database.

    Sensor measures are types of readings that sensors can report. For instance
    "temperature", "electricity consumption", or "air flow".

    Args:
        name: Name of this measure, e.g. "temperature".
        units: Units in which this measure is specified.
        datatype: Value type of this location identifier. Has to be one of "string",
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
    readings, timestamps, sensor_uniq_id, measure_name, session=None
):
    """Insert sensor readings to the database.

    Args:
        readings: Readings to insert. An iterable.
        timestamps: Timestamps associated with the readings. An iterable of the same
            length as readings.
        sensor_uniq_id: Unique identifier for the sensor that reports these readings.
        measure_name: Name of the sensor measure that these are readings for.
        session: SQLAlchemy session. Optional.

    Returns:
        None
    """
    if len(readings) != len(timestamps):
        raise ValueError(
            f"There should be as many readings as there are timestamps, but got {len(readings)} and {len(timestamps)}"
        )
    if len(readings) == 0:
        return None

    # Check the type of readings to insert.
    example_element = readings[0]
    readings_class = utils.get_value_class_from_instance_type(example_element)
    if readings_class is None:
        msg = (
            f"Don't know how to insert sensor readings of type {type(example_element)}."
        )
        raise ValueError(msg)

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
            f"Measure '{measure_name}' is not a valid measure for sensor {sensor_uniq_id}."
        )
    expected_datatype = measures_result[0][0]

    # Check that the data type is correct
    datatype_matches = utils.check_datatype(example_element, datatype_expected)
    if not datatype_matches:
        raise ValueError(
            f"For sensor measure '{measure_name}' expected a readings of type "
            f"{datatype_expected} but got a {type(example_element)}."
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
