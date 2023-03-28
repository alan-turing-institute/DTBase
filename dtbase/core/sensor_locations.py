"""Functions for accessing the sensor_location table."""
import sqlalchemy as sqla

from dtbase.backend.utils import add_default_session
from dtbase.core import queries, sensors
from dtbase.core.structure import Location, LocationSchema, Sensor, SensorLocation
from dtbase.core import utils


@add_default_session
def insert_sensor_location(
    sensor_uniq_id,
    schema_name,
    coordinates,
    installation_datetime,
    session=None,
):
    """Add a sensor location installation.

    Args:
        sensor_uniq_id: Unique identifier of the sensor.
        schema_name: Name of the location schema
        coordinates: Coordinates of the location, as a dictionary, with keys
            being measure names.
        installation_datetime: Date from which onwards the sensor has been at this
            location.
        session: Optional. SQLAlchemy session.

    Returns:
        None
    """
    sensor_id = sensors.sensor_id_from_unique_identifier(
        sensor_uniq_id, session=session
    )
    location_query = queries.select_location_by_coordinates(
        schema_name, session=session, **coordinates
    )
    result = session.execute(location_query).first()
    if result is None:
        raise ValueError(
            f"No location with schema '{schema_name}' and coordinates "
            f"{coordinates}."
        )
    location_id = result[0]
    session.add(
        SensorLocation(
            sensor_id=sensor_id,
            location_id=location_id,
            installation_datetime=installation_datetime,
        )
    )
    session.flush()


@add_default_session
def get_location_history(sensor_uniq_id, session=None):
    """Location history of one sensor.

    Args:
        sensor_uniq_id: Unique identifier of the sensor.
        session: Optional. SQLAlchemy session.


    Returns:
        A list of dictionaries, naming the coordinates where this sensor was installed
        at different times.
    """
    query = (
        sqla.select(
            SensorLocation.installation_datetime,
            SensorLocation.location_id,
            LocationSchema.name.label("schema_name"),
        )
        .join(Sensor, Sensor.id == SensorLocation.sensor_id)
        .where(Sensor.unique_identifier == sensor_uniq_id)
        .join(Location, Location.id == SensorLocation.location_id)
        .join(LocationSchema, LocationSchema.id == Location.schema_id)
        .order_by(SensorLocation.installation_datetime.desc())
    )
    query_result = session.execute(query).fetchall()
    result = []
    for installation_datetime, location_id, schema_name in query_result:
        location_sq = queries.select_location_by_coordinates(
            schema_name, session
        ).subquery()
        location_query = sqla.select(location_sq).where(location_sq.c.id == location_id)
        location_result = session.execute(location_query).mappings().all()
        location_result = utils.row_mappings_to_dicts(location_result)[0]
        location_result["installation_datetime"] = installation_datetime
        result.append(location_result)
    return result
