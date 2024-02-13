"""Functions for accessing the sensor tables. """
import datetime as dt
from typing import Any, List, Optional, Sequence

import sqlalchemy as sqla

from dtbase.backend.utils import Session
from dtbase.core import queries, utils
from dtbase.core.exc import RowMissingError
from dtbase.core.structure import (
    Sensor,
    SensorMeasure,
    SensorType,
    SensorTypeMeasureRelation,
)


def measure_id_from_name_and_units(
    measure_name: str, measure_units: str, session: Session
) -> Any:
    """
    Find the id of a sensor measure of the given name and units.
    (Note that our uniqueness constraint is on the name+units combination)

    Args:
        measure_name: Name of the sensor measure
        measure_units: Name of the sensor measure
        session: SQLAlchemy session. Optional.

    Returns:
        Database id of the sensor measure.
    """
    query = sqla.select(SensorMeasure.id).where(
        (SensorMeasure.name == measure_name) & (SensorMeasure.units == measure_units)
    )
    result = session.execute(query).fetchall()
    if len(result) == 0:
        raise ValueError(
            f"No sensor measure named '{measure_name}' with units '{measure_units}'"
        )
    if len(result) > 1:
        raise ValueError(
            f"Multiple sensor measures named '{measure_name}' with units "
            f"'{measure_units}'"
        )
    return result[0][0]


def type_id_from_name(type_name: str, session: Session) -> Any:
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


def sensor_id_from_unique_identifier(unique_identifier: str, session: Session) -> Any:
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


def insert_sensor_measure(
    name: str,
    units: str,
    datatype: str | int | int | float,
    session: Session,
) -> None:
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
        measure_id: int, PK of the newly created measure.
    """
    if datatype not in ("string", "integer", "float", "boolean"):
        raise ValueError(f"Unrecognised data type: {datatype}")
    session.add(SensorMeasure(name=name, units=units, datatype=datatype))
    session.flush()


def insert_sensor_type(
    name: str,
    description: str,
    measures: list[dict[str, Optional[str]]],
    session: Session,
) -> None:
    """Insert a new sensor type into the database.

    Sensor type specifies a set of measures that sensors of this type can report. For
    instance, an atmospheric sensor might report temperature and air pressure. Sensor
    types can also have a name and a free form description.

    Args:
        name: Name of this sensor type
        description: Free form text description, for human consumption.
        measures: List of sensor measures that this sensor type can report.
            This should be a list of dicts with keys 'name' and 'units', that
            correspond to existing measures in the database.
        session: SQLAlchemy session. Optional.

    Returns:
        None
    """
    new_type = SensorType(name=name, description=description)
    session.add(new_type)
    session.flush()
    for measure in measures:
        measure_id = measure_id_from_name_and_units(
            measure["name"], measure["units"], session=session
        )
        session.add(
            SensorTypeMeasureRelation(type_id=new_type.id, measure_id=measure_id)
        )
    session.flush()


def insert_sensor(
    type_name: str,
    unique_identifier: str,
    session: Session,
    name: Optional[str] = None,
    notes: Optional[str] = None,
) -> None:
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


def insert_sensor_readings(
    measure_name: str,
    unique_identifier: str,
    readings: list,
    timestamps: list[dt.datetime],
    session: Session,
) -> None:
    """Insert sensor readings to the database.

    Args:
        measure_name: Name of the sensor measure that these are readings for.
        unique_identifier: Unique identifier for the sensor that reports these readings.
        readings: Readings to insert. An iterable.
        timestamps: Timestamps associated with the readings. An iterable of the same
            length as readings.
        session: SQLAlchemy session. Optional.

    Returns:
        None

    Note that there can be two sensor measures with the same name (but
    different units), so we look at the sensor_type to disambiguate.
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
        .where(Sensor.unique_identifier == unique_identifier)
    )
    measures_result = session.execute(measures_q).fetchall()
    valid_measure = len(measures_result) > 0
    if not valid_measure:
        raise ValueError(
            f"Measure '{measure_name}' is not a valid measure for sensor "
            f"'{unique_identifier}'."
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
    measures_for_sensor = get_measures_for_sensor_identifier(
        unique_identifier, session=session
    )
    measure_units = next(
        m["units"] for m in measures_for_sensor if m["name"] == measure_name
    )
    measure_id = measure_id_from_name_and_units(
        measure_name, measure_units, session=session
    )
    sensor_id = sensor_id_from_unique_identifier(unique_identifier, session=session)
    rows = [
        {
            "value": value,
            "timestamp": timestamp,
            "sensor_id": sensor_id,
            "measure_id": measure_id,
        }
        for value, timestamp in zip(readings, timestamps)
    ]
    session.execute(
        sqla.dialects.postgresql.insert(
            readings_class.__table__
        ).on_conflict_do_nothing(),
        rows,
    )
    session.flush()


def get_measures_for_sensor_identifier(unique_identifier: str, session: Session) -> Any:
    """
    Get list of sensor measures for a sensor

    Args:
        unique_identifier:str, id of the sensor
        session: SQLAlchemy session. Optional.
    Returns:
        measure_list:list of dicts, each with keys "id","name","units","datatype"
    """
    all_types = list_sensor_types(session=session)
    query = sqla.select(
        Sensor.type_id,
    ).where(Sensor.unique_identifier == unique_identifier)
    result = session.execute(query).fetchall()
    sensor_type = next(st for st in all_types if st["id"] == result[0][0])
    if sensor_type:
        return sensor_type["measures"]
    else:
        return []


def get_datatype_by_measure_name(measure_name: str, session: Session) -> Any:
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


def get_sensor_readings(
    measure_name: str,
    unique_identifier: str,
    dt_from: dt.datetime,
    dt_to: dt.datetime,
    session: Session,
) -> Sequence:
    """Get sensor readings from the database.

    Args:
        measure_name: Name of the sensor measure to get readings for.
        unique_identifier: Unique identifier for the sensor to get readings for.
        dt_from: Datetime object for earliest readings to get. Inclusive.
        dt_to: Datetime object for last readings to get. Inclusive.
        session: SQLAlchemy session. Optional.

    Returns:
        Readings from the database. A list of tuples [(value, timestamp), ...]
    """
    datatype_name = get_datatype_by_measure_name(measure_name, session=session)
    value_class = utils.sensor_reading_class_dict[datatype_name]
    query = (
        sqla.select(value_class.value, value_class.timestamp)
        .join(Sensor, Sensor.id == value_class.sensor_id)
        .join(SensorMeasure, SensorMeasure.id == value_class.measure_id)
        .where(
            (Sensor.unique_identifier == unique_identifier)
            & (SensorMeasure.name == measure_name)
            & (value_class.timestamp >= dt_from)
            & (value_class.timestamp <= dt_to)
        )
    )
    result = session.execute(query).fetchall()
    return result


def delete_sensor(unique_identifier: str, session: Session) -> None:
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


def delete_sensor_measure(measure_name: str, session: Session) -> None:
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


def delete_sensor_type(type_name: str, session: Session) -> None:
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


def list_sensor_measures(session: Session) -> List[dict]:
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


def list_sensor_types(session: Session) -> List[dict]:
    """List all sensor types.

    Args:
        session: SQLAlchemy session. Optional.

    Returns:
        List of all sensor types, each of which contains a dict of measures
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


def list_sensors(session: Session, type_name: Optional[str] = None) -> List[dict]:
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


def edit_sensor(
    unique_identifier: str,
    new_name: str,
    new_notes: str,
    session: Session,
) -> None:
    """Edit an existing sensor in the database.

    Args:
        unique_identifier: Unique identifier of the sensor to be edited.
        new_name: New name for the sensor.
        new_notes: New notes for the sensor.
        session: SQLAlchemy session. Optional.

    Returns:
        None
    """
    # Find the sensor by unique identifier
    sensor = (
        session.query(Sensor).filter_by(unique_identifier=unique_identifier).first()
    )

    if sensor is not None:
        # Update the attributes
        sensor.name = new_name
        sensor.notes = new_notes
    else:
        raise RowMissingError(
            f"No sensor found with unique identifier {unique_identifier}"
        )
