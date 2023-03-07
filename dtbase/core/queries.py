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
