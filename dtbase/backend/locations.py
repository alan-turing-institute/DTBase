"""Functions for accessing the locations tables. """
from sqlalchemy import and_, case, func
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
    LocationSchemaIdentifier,
    LocationStringValue,
)
from dtbase.core.structure import SQLA as db


@add_default_session
def insert_location_value(value, location_id, identifier_id, session=None):
    value_class = (
        LocationBooleanValue
        if isinstance(value, bool)
        else LocationFloatValue
        if isinstance(value, float)
        else LocationIntegerValue
        if isinstance(value, int)
        else LocationStringValue
        if isinstance(value, str)
        else None
    )
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
            LocationSchemaIdentifier(
                schema_id=new_schema.id, identifier_id=identifier_id
            )
        )
    session.flush()
