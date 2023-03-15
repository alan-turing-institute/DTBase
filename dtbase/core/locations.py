"""Functions for accessing the locations tables. """
import sqlalchemy as sqla

from dtbase.backend.utils import add_default_session
from dtbase.core import queries
from dtbase.core.structure import (
    Location,
    LocationBooleanValue,
    LocationFloatValue,
    LocationIdentifier,
    LocationIntegerValue,
    LocationSchema,
    LocationSchemaIdentifierRelation,
    LocationStringValue,
)
from dtbase.core import utils


@add_default_session
def insert_location_value(value, location_id, identifier_id, session=None):
    """Insert a coordinate for a location into the database.

    Args:
        value: Value of the coordinate
        location_id: Id of the location for which this is the coordinate
        identifier_id: Id of the location identifier this a coordinate for
        session: SQLAlchemy session. Optional.

    Returns:
        None
    """
    value_class = utils.get_value_class_from_instance_type(value)
    if value_class is None:
        msg = f"Don't know how to insert location values of type {type(value)}."
        raise ValueError(msg)
    session.add(
        value_class(location_id=location_id, identifier_id=identifier_id, value=value)
    )
    session.flush()


@add_default_session
def identifier_id_from_name(identifier_name, session=None):
    """Find the id of a location identifier of the given name.

    Args:
        identifier_name: Name of the location identifier
        session: SQLAlchemy session. Optional.

    Returns:
        Database id of the location identifier.
    """
    query = sqla.select(LocationIdentifier.id).where(
        LocationIdentifier.name == identifier_name
    )
    result = session.execute(query).fetchall()
    if len(result) == 0:
        raise ValueError(f"No location identifier named {identifier_name}")
    if len(result) > 1:
        raise ValueError(f"Multiple location identifiers named {identifier_name}")
    return result[0][0]


@add_default_session
def schema_id_from_name(schema_name, session=None):
    """Find the id of a location schema of the given name.

    Args:
        schema_name: Name of the location schema
        session: SQLAlchemy session. Optional.

    Returns:
        Database id of the location schema.
    """
    query = sqla.select(LocationSchema.id).where(LocationSchema.name == schema_name)
    result = session.execute(query).fetchall()
    if len(result) == 0:
        raise ValueError(f"No location schema named {schema_name}")
    if len(result) > 1:
        raise ValueError(f"Multiple location schemas named {schema_name}")
    return result[0][0]


@add_default_session
def insert_location(schema_name, session=None, **kwargs):
    """Insert a new location into the database.

    Args:
        schema_name: Name of the location schema that this location uses.
        session: SQLAlchemy session. Optional.
        keyword arguments: Coordinates of this location. Which keyword arguments need to
            be provided by the schema. For instance, if the schema says that locations
            are specified by coordinates x, y, and z, then the keyword argument should
            be x, y, and z.

    Returns:
        None
    """
    schema_id = schema_id_from_name(schema_name, session=session)
    # Check that all the right identifiers are specified for this schema.
    identifiers_sq = queries.location_identifiers_by_schema().subquery()
    identifiers_q = sqla.select(
        identifiers_sq.c.identifier_id,
        identifiers_sq.c.identifier_name,
        identifiers_sq.c.identifier_datatype,
    ).where(identifiers_sq.c.schema_id == schema_id)
    identifiers_result = session.execute(identifiers_q).fetchall()
    identifiers_expected = set(x[1] for x in identifiers_result)
    identifiers_specified = set(kwargs.keys())
    # Check that exactly the right identifiers are given
    if identifiers_expected != identifiers_specified:
        raise ValueError(
            f"For schema {schema_name} expected to receive location identifiers "
            f"{identifiers_expected} but got {identifiers_specified}."
        )
    # Check that the data types are correct
    for _, identifier_name, datatype_expected in identifiers_result:
        value = kwargs[identifier_name]
        datatype_matches = utils.check_datatype(value, datatype_expected)
        if not datatype_matches:
            raise ValueError(
                f"For location identifier '{identifier_name}' expected a value of type "
                f"{datatype_expected} but got a {type(value)}."
            )

    # Check that this location doesn't exist yet.
    current_locations = session.execute(
        queries.select_location_by_coordinates(schema_name, session, **kwargs)
    ).fetchall()
    if len(current_locations) > 0:
        raise ValueError(
            f"Location with schema '{schema_name}' and coordinates "
            f"{kwargs} already exists."
        )

    # Make the new location and set its coordinates
    new_location = Location(schema_id=schema_id)
    session.add(new_location)
    session.flush()
    for identifier_id, identifier_name, _ in identifiers_result:
        value = kwargs[identifier_name]
        insert_location_value(value, new_location.id, identifier_id, session=session)


@add_default_session
def insert_location_identifier(name, units, datatype, session=None):
    """Insert a new location identifier into the database.

    Location identifiers are types of coordinates by which locations can be set and
    identified. For instance "shelf number", "latitude", or "y-coordinate."

    Args:
        name: Name of this location identifier. For example "y-coordinate".
        units: Units in which this location identifier is measured.
        datatype: Value type of this location identifier. Has to be one of "string",
            "integer", "float", or "boolean".
        session: SQLAlchemy session. Optional.

    Returns:
        None
    """
    if datatype not in ("string", "integer", "float", "boolean"):
        raise ValueError(f"Unrecognised data type: {datatype}")
    session.add(LocationIdentifier(name=name, units=units, datatype=datatype))
    session.flush()


@add_default_session
def insert_location_schema(name, description, identifiers, session=None):
    """Insert a new location schema into the database.

    Location schema specifies a set of identifiers by which locations are identified
    uniquely. For instance, schema might say that locations are identified by latitude,
    longitude, and height from sea level. Another schema might say that locations are
    identified by aisle, column, and shelf (in a warehouse).

    Args:
        name: Name of this location schema.
        description: Free form text description, for human consumption.
        identifiers: List of identifiers that this schema uses to identify locations.
            This should be a list of strings, that are the names of existing location
            identifiers in the database.
        session: SQLAlchemy session. Optional.

    Returns:
        None
    """
    new_schema = LocationSchema(name=name, description=description)
    session.add(new_schema)
    session.flush()
    for identifier_name in identifiers:
        identifier_id = identifier_id_from_name(identifier_name, session=session)
        session.add(
            LocationSchemaIdentifierRelation(
                schema_id=new_schema.id, identifier_id=identifier_id
            )
        )
    session.flush()


@add_default_session
def delete_location_by_id(location_id, session=None):
    """Delete a location from the database, identified by its primary key id.

    Also deletes any coordinate values for this location.

    Args:
        location_id: Primary key id of the location to delete.
        session: SQLAlchemy session. Optional.

    Returns:
        None
    """
    for value_class in (
        LocationStringValue,
        LocationIntegerValue,
        LocationFloatValue,
        LocationBooleanValue,
    ):
        session.execute(
            sqla.delete(value_class).where(value_class.location_id == location_id)
        )
    session.execute(sqla.delete(Location).where(Location.id == location_id))


@add_default_session
def delete_location_by_coordinates(schema_name, session=None, **kwargs):
    """Delete a location from the database, identified by its coordinates.

    Also deletes any coordinate values for this location.

    Args:
        schema_name: Name of the location schema for this location.
        session: SQLAlchemy session. Optional.
        keyword arguments: Coordinates for this location. See docstring of
            `insert_location` for more information.

    Returns:
        None
    """
    location_query = queries.select_location_by_coordinates(
        schema_name, session, **kwargs
    )
    location_id = session.execute(location_query).fetchall()
    if not location_id:
        raise ValueError(f"Location not found: {schema_name}, {kwargs}")
    delete_location_by_id(location_id[0][0], session=session)


@add_default_session
def delete_location_identifier(identifier_name, session=None):
    raise NotImplemented("Deleting location identifiers not yet implemented.")


@add_default_session
def delete_location_schema(schema_name, session=None):
    raise NotImplemented("Deleting location schemas not yet implemented.")


@add_default_session
def list_locations(schema_name, session=None, **kwargs):
    """List all locations in a schema, optionally filtering by coordinates.

    With `list_locations(schema_name)`, all locations in a schema will be returned.
    Additional keyword arguments can fix some coordinates, e.g.
    `list_locations("latlong", latitude=0)` would list all locations with latitude=0.

    Args:
        schema_name: Name of the location schema.
        session: SQLAlchemy session. Optional.
        keyword arguments: Coordinates for the locations to list. Optional. See
        docstring of `insert_location` for more.

    Returns:
        List of all the locations that match the provided arguments, i.e. are of the
        specified schema and have the coordinate values specified in the keyword
        arguments.
    """
    query = queries.select_location_by_coordinates(schema_name, session, **kwargs)
    locations = session.execute(query).mappings().all()
    return locations
