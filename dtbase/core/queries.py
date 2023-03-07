"""Functions for building various database queries.

Each function returns a SQLAlchemy Query object. Turning these into subqueries or CTEs
or executing them is the responsibility of the caller.
"""
from sqlalchemy import and_, case, func
from sqlalchemy.orm import aliased, Query

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


def location_identifiers_by_schema(session):
    """Query for identifiers of locations by schema."""
    query = (
        session.query(
            LocationSchema.id.label("schema_id"),
            LocationSchema.name.label("schema_name"),
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
    )
    return query


def select_location_by_coordinates(schema_name, session, **kwargs):
    schema_sq = location_identifiers_by_schema(session).subquery()
    schema_q = session.query(
        schema_sq.c.identifier_id,
        schema_sq.c.identifier_name,
        schema_sq.c.identifier_datatype,
    ).where(schema_sq.c.schema_name == schema_name)
    identifiers = session.execute(schema_q).fetchall()
    location_q = session.query(Location.id)
    for id_id, id_name, id_datatype in identifiers:
        value_class = aliased(utils.get_value_class_from_type_name(id_datatype))
        location_q = location_q.join(
            value_class,
            and_(
                value_class.location_id == Location.id,
                value_class.value == kwargs[id_name],
                value_class.identifier_id == id_id,
            ),
        )
    return location_q
