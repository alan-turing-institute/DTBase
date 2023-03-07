"""Functions for accessing the locations tables. """
from sqlalchemy import and_, case, delete, func
from sqlalchemy.orm import aliased, Query

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
from dtbase.core.structure import SQLA as db
from dtbase.core import utils


@add_default_session
def insert_location_value(value, location_id, identifier_id, session=None):
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
    query = session.query(LocationIdentifier.id).where(
        LocationIdentifier.name == identifier_name
    )
    identifier_id = session.execute(query).fetchone()[0]
    return identifier_id


@add_default_session
def schema_id_from_name(schema_name, session=None):
    query = session.query(LocationSchema.id).where(LocationSchema.name == schema_name)
    schema_id = session.execute(query).fetchone()[0]
    return schema_id


@add_default_session
def insert_location(schema_name, session=None, **kwargs):
    schema_id = schema_id_from_name(schema_name, session=session)
    new_location = Location(schema_id=schema_id)
    session.add(new_location)
    session.flush()
    for identifier_name, value in kwargs.items():
        identifier_id = identifier_id_from_name(identifier_name, session=session)
        insert_location_value(value, new_location.id, identifier_id, session=session)


@add_default_session
def insert_location_identifier(name, units, datatype, session=None):
    session.add(LocationIdentifier(name=name, units=units, datatype=datatype))
    session.flush()


@add_default_session
def insert_location_schema(name, description, identifiers, session=None):
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
    for value_class in (
        LocationStringValue,
        LocationIntegerValue,
        LocationFloatValue,
        LocationBooleanValue,
    ):
        session.execute(
            delete(value_class).where(value_class.location_id == location_id)
        )
    session.execute(delete(Location).where(Location.id == location_id))


@add_default_session
def delete_location_by_coordinates(schema_name, session=None, **kwargs):
    location_query = queries.select_location_by_coordinates(
        schema_name, session, **kwargs
    )
    location_id = session.execute(location_query).fetchall()
    if not location_id:
        raise ValueError(f"Location not found: {kwargs}")
    delete_location_by_id(location_id[0][0], session=session)
