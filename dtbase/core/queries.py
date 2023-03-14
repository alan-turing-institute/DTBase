"""Functions for building various database queries.

Each function returns a SQLAlchemy Query object. Turning these into subqueries or CTEs
or executing them is the responsibility of the caller.
"""
import sqlalchemy as sqla
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


def location_identifiers_by_schema():
    """Query for identifiers of locations by schema."""
    query = (
        sqla.select(
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
    """Query for locations and their coordinates.

    Return a query with the column `id` and one column for each location identifier for
    this location schema. Each row is a location. Keyword arguments can be used to
    filter by the location identifiers, e.g. with no keyword arguments the query will
    return all locations in this schema, and with all location identifiers specified in
    the keyword arguments the query will return a single location.

    For instance, `select_location_by_coordinates("latlong", latitude=0)` will return a
    query for "latlong" locations that have latitude=0.

    Note that in the process of constructing this query another query needs to be
    executed.
    """
    # Find the identifiers for this schema.
    schema_sq = location_identifiers_by_schema().subquery()
    schema_q = sqla.select(
        schema_sq.c.identifier_id,
        schema_sq.c.identifier_name,
        schema_sq.c.identifier_datatype,
    ).where(schema_sq.c.schema_name == schema_name)
    identifiers = session.execute(schema_q).fetchall()

    # Check that no extraneous keyword arguments are given.
    identifier_names = set(x[1] for x in identifiers)
    for key in kwargs:
        if key not in identifier_names:
            msg = f"Location identifier '{key}' not valid for schema '{schema_name}'"
            raise ValueError(msg)

    # Create the query for locations.
    columns = [Location.id]
    joins = []
    for id_id, id_name, id_datatype in identifiers:
        value_class = aliased(utils.get_value_class_from_type_name(id_datatype))
        columns.append(value_class.value.label(id_name))
        join_conditions = [
            value_class.location_id == Location.id,
            value_class.identifier_id == id_id,
        ]
        if id_name in kwargs:
            join_conditions.append(value_class.value == kwargs[id_name])
        joins.append((value_class, sqla.and_(*join_conditions)))
    location_q = sqla.select(*columns)
    for join in joins:
        location_q = location_q.join(*join)
    return location_q
