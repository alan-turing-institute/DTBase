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


def location_identifiers(session):
    """Query for identifiers of locations."""
    query = (
        session.query(
            Location.id.label("location_id"),
            LocationIdentifier.id.label("identifier_id"),
            LocationIdentifier.name.label("identifier_name"),
            LocationIdentifier.unit.label("identifier_unit"),
            LocationIdentifier.datatype.label("identifier_datatype"),
        )
        .join(
            LocationSchemaIdentifierRelation,
            LocationSchemaIdentifierRelation.schema_id == Location.schema_id,
        )
        .join(
            LocationIdentifier,
            LocationIdentifier.id == LocationSchemaIdentifierRelation.identifier_id,
        )
    )
    return query


def location_value(session):
    location_identifiers_sq = location_identifiers(session).subquery()
    # TODO Finish this
