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


def get_value_class_from_instance_type(value):
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
    return value_class


def get_value_class_from_type_name(name):
    value_class = (
        LocationBooleanValue
        if name == "bool"
        else LocationFloatValue
        if name == "float"
        else LocationIntegerValue
        if name == "int"
        else LocationStringValue
        if name == "string"
        else None
    )
    return value_class


@add_default_session
def insert_location_value(value, location_id, identifier_id, session=None):
    value_class = get_value_class_from_instance_type(value)
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
def select_location_by_coordinates(schema_name, session=None, **kwargs):
    schema_sq = queries.location_identifiers_by_schema(session).subquery()
    schema_q = session.query(
        schema_sq.c.identifier_id,
        schema_sq.c.identifier_name,
        schema_sq.c.identifier_datatype,
    ).where(schema_sq.c.schema_name == schema_name)
    identifiers = session.execute(schema_q).fetchall()
    location_q = session.query(Location.id)
    for id_id, id_name, id_datatype in identifiers:
        value_class = aliased(get_value_class_from_type_name(id_datatype))
        location_q = location_q.join(
            value_class,
            and_(
                value_class.location_id == Location.id,
                value_class.value == kwargs[id_name],
                value_class.identifier_id == id_id,
            ),
        )
    return session.execute(location_q).fetchall()


@add_default_session
def delete_location_by_id(location_id, session=None):
    session.execute(
        delete(LocationStringValue).where(
            LocationStringValue.location_id == location_id
        )
    )
    session.execute(
        delete(LocationIntegerValue).where(
            LocationIntegerValue.location_id == location_id
        )
    )
    session.execute(
        delete(LocationFloatValue).where(LocationFloatValue.location_id == location_id)
    )
    session.execute(
        delete(LocationBooleanValue).where(
            LocationBooleanValue.location_id == location_id
        )
    )
    session.execute(delete(Location).where(Location.id == location_id))


@add_default_session
def delete_location_by_coordinates(schema_name, session=None, **kwargs):
    location_id = select_location_by_coordinates(schema_name, session=session, **kwargs)
    if not location_id:
        raise ValueError(f"Location not found: {kwargs}")
    delete_location_by_id(location_id[0][0], session=session)
