"""Functions for accessing the locations tables. """
from typing import Any, Dict, List, Optional

import sqlalchemy as sqla

from dtbase.backend.utils import Session, default_session
from dtbase.core import queries, utils
from dtbase.core.exc import RowExistsError, RowMissingError, TooManyRowsError
from dtbase.core.structure import (
    Location,
    LocationIdentifier,
    LocationSchema,
    LocationSchemaIdentifierRelation,
)


def insert_location_value(
    value: (float | str),
    location_id: str,
    identifier_id: str,
    session: Optional[Session] = None,
) -> None:
    """Insert a coordinate for a location into the database.

    Args:
        value: Value of the coordinate
        location_id: Id of the location for which this is the coordinate
        identifier_id: Id of the location identifier this a coordinate for
        session: SQLAlchemy session. Optional.

    Returns:
        None
    """
    session = default_session(session)
    value_type = type(value)
    if value_type not in utils.location_value_class_dict:
        msg = f"Don't know how to insert location values of type {value_type}."
        raise ValueError(msg)
    value_class = utils.location_value_class_dict[value_type]
    session.add(
        value_class(location_id=location_id, identifier_id=identifier_id, value=value)
    )
    session.flush()


def identifier_id_from_name(
    identifier_name: str, session: Optional[Session] = None
) -> None:
    """Find the id of a location identifier of the given name.

    Args:
        identifier_name: Name of the location identifier
        session: SQLAlchemy session. Optional.

    Returns:
        Database id of the location identifier.
    """
    session = default_session(session)
    query = sqla.select(LocationIdentifier.id).where(
        LocationIdentifier.name == identifier_name
    )
    result = session.execute(query).fetchall()
    if len(result) == 0:
        raise RowMissingError(f"No location identifier '{identifier_name}'")
    if len(result) > 1:
        raise TooManyRowsError(f"Multiple location identifiers named {identifier_name}")
    return result[0][0]


def schema_id_from_name(schema_name: str, session: Optional[Session] = None) -> None:
    """Find the id of a location schema of the given name.

    Args:
        schema_name: Name of the location schema
        session: SQLAlchemy session. Optional.

    Returns:
        Database id of the location schema.
    """
    session = default_session(session)
    query = sqla.select(LocationSchema.id).where(LocationSchema.name == schema_name)
    result = session.execute(query).fetchall()
    if len(result) == 0:
        raise RowMissingError(f"No location schema '{schema_name}'")
    if len(result) > 1:
        raise TooManyRowsError(f"Multiple location schemas named {schema_name}")
    return result[0][0]


def insert_location(
    schema_name: str, session: Optional[Session] = None, **kwargs: Any
) -> None:
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
    session = default_session(session)
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
        raise RowExistsError(
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


def insert_location_identifier(
    name: str,
    units: str,
    datatype: (str | int | float | bool),
    session: Optional[Session] = None,
) -> None:
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
    session = default_session(session)
    if datatype not in ("string", "integer", "float", "boolean"):
        raise ValueError(f"Unrecognised data type: {datatype}")

    # Check if an identifier with the same name and units already exists
    existing_identifier = (
        session.query(LocationIdentifier)
        .filter(LocationIdentifier.name == name, LocationIdentifier.units == units)
        .first()
    )

    # Only add a new identifier if one with the same name and units does not already
    # exist
    if not existing_identifier:
        new_identifier = LocationIdentifier(name=name, units=units, datatype=datatype)
        session.add(new_identifier)
        session.flush()


def insert_location_schema(
    name: str,
    description: str,
    identifiers: List[str],
    session: Optional[Session] = None,
) -> None:
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
    session = default_session(session)
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


def delete_location_by_id(location_id: str, session: Optional[Session] = None) -> None:
    """Delete a location from the database, identified by its primary key id.

    Also deletes any coordinate values for this location.

    Args:
        location_id: Primary key id of the location to delete.
        session: SQLAlchemy session. Optional.

    Returns:
        None
    """
    session = default_session(session)
    result = session.execute(sqla.delete(Location).where(Location.id == location_id))
    if result.rowcount == 0:
        raise RowMissingError(f"No location with ID {location_id}")


def delete_location_by_coordinates(
    schema_name: str, session: Optional[Session] = None, **kwargs: Any
) -> None:
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
    session = default_session(session)
    location_query = queries.select_location_by_coordinates(
        schema_name, session, **kwargs
    )
    location_id = session.execute(location_query).fetchall()
    if not location_id:
        raise RowMissingError(f"Location not found: {schema_name}, {kwargs}")
    delete_location_by_id(location_id[0][0], session=session)


def delete_location_identifier(
    identifier_name: str, session: Optional[Session] = None
) -> None:
    """Delete a location identifier from the database.

    Raises an error if a schema exists that uses this identifier.

    Args:
        identifier_name: Name of the location identifier to delete.
        session: SQLAlchemy session. Optional.

    Returns:
        None
    """
    session = default_session(session)
    result = session.execute(
        sqla.delete(LocationIdentifier).where(
            LocationIdentifier.name == identifier_name
        )
    )
    if result.rowcount == 0:
        raise RowMissingError(f"No location identifier '{identifier_name}'")


def delete_location_schema(schema_name: str, session: Optional[Session] = None) -> None:
    """Delete a location schema from the database.

    Raises an error if a location exists that uses this schema.

    Args:
        identifier_name: Name of the location schema to delete.
        session: SQLAlchemy session. Optional.

    Returns:
        None
    """
    session = default_session(session)
    result = session.execute(
        sqla.delete(LocationSchema).where(LocationSchema.name == schema_name)
    )
    if result.rowcount == 0:
        raise RowMissingError(f"No location schema '{schema_name}'")


def list_location_identifiers(session: Optional[Session] = None) -> List[dict]:
    """List all location identifiers

    Args:
        session: SQLAlchemy session. Optional.

    Returns:
        List of all location identifiers
    """
    session = default_session(session)
    result = (
        session.execute(
            sqla.select(
                LocationIdentifier.id,
                LocationIdentifier.name,
                LocationIdentifier.units,
                LocationIdentifier.datatype,
            )
        )
        .mappings()
        .all()
    )
    result = utils.row_mappings_to_dicts(result)
    return result


def list_location_schemas(session: Optional[Session] = None) -> List[dict]:
    """List all location schemas with their identifiers

    Args:
        session: SQLAlchemy session. Optional.

    Returns:
        List of all location schemas with their identifiers
    """
    session = default_session(session)
    result = (
        session.query(
            LocationSchema.id,
            LocationSchema.name,
            LocationSchema.description,
            LocationIdentifier.id.label("identifier_id"),
            LocationIdentifier.name.label("identifier_name"),
            LocationIdentifier.units.label("identifier_units"),
            LocationIdentifier.datatype.label("identifier_datatype"),
        )
        .join(
            LocationSchemaIdentifierRelation,
            LocationSchemaIdentifierRelation.schema_id == LocationSchema.id,
        )
        .join(
            LocationIdentifier,
            LocationIdentifier.id == LocationSchemaIdentifierRelation.identifier_id,
        )
        .all()
    )

    # transform result into a list of schemas with their identifiers
    schemas = []
    current_schema_id = None
    for row in result:
        if row.id != current_schema_id:
            current_schema_id = row.id
            schema = {
                "id": row.id,
                "name": row.name,
                "description": row.description,
                "identifiers": [],
            }
            schemas.append(schema)
        identifier = {
            "id": row.identifier_id,
            "name": row.identifier_name,
            "unit": row.identifier_units,
            "datatype": row.identifier_datatype,
        }
        schema["identifiers"].append(identifier)
    return schemas


def list_locations(
    schema_name: str, session: Optional[Session] = None, **kwargs: Any
) -> List[dict]:
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
    session = default_session(session)
    query = queries.select_location_by_coordinates(schema_name, session, **kwargs)
    result = session.execute(query).mappings().all()
    result = utils.row_mappings_to_dicts(result)
    return result


def get_schema_details(
    schema_name: str, session: Optional[Session] = None
) -> Dict[str, list]:
    """Fetch details of a location schema from the database, including the identifiers
    associated with the schema.

    Args:
        schema_id: Name of the location schema.
        session: SQLAlchemy session. Optional.

    Returns:
        Dictionary with keys 'id', 'name', 'description', and 'identifiers'.
        'identifiers' is a list of identifiers
        (dictionaries with keys 'id', 'name', 'unit', 'datatype').
    """
    session = default_session(session)
    schema = (
        session.query(
            LocationSchema.id, LocationSchema.name, LocationSchema.description
        )
        .filter(LocationSchema.name == schema_name)  # Change made here
        .first()
    )
    if not schema:
        raise RowMissingError("No such schema")
    schema_result = dict(schema._mapping)

    identifiers = (
        session.query(
            LocationIdentifier.id,
            LocationIdentifier.name,
            LocationIdentifier.units,
            LocationIdentifier.datatype,
        )
        .join(LocationSchemaIdentifierRelation)
        .filter(
            LocationSchemaIdentifierRelation.schema_id == schema.id
        )  # schema.id from the fetched schema
        .all()
    )
    identifiers_result = [dict(identifier._mapping) for identifier in identifiers]

    schema_result["identifiers"] = identifiers_result
    return schema_result
