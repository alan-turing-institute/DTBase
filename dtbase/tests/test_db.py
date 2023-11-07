"""
Test the basic structure of the database, creating rows and relations via
the SQLAlchemy ORM.
"""

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


def test_add_zadf_location(session):
    si = LocationIdentifier(name="zone", datatype="string")
    ii = LocationIdentifier(name="aisle", datatype="integer")
    fi = LocationIdentifier(name="distance", units="m", datatype="float")
    bi = LocationIdentifier(name="upper shelf", datatype="boolean")
    session.add(si)
    session.add(ii)
    session.add(fi)
    session.add(bi)
    session.commit()
    assert isinstance(si.id, int)
    assert isinstance(ii.id, int)
    assert isinstance(fi.id, int)
    assert isinstance(bi.id, int)

    schema = LocationSchema(name="zone-aisle-distance-shelf")
    session.add(schema)
    session.commit()
    assert isinstance(schema.id, int)

    sid_s = LocationSchemaIdentifierRelation(schema_id=schema.id, identifier_id=si.id)
    sid_i = LocationSchemaIdentifierRelation(schema_id=schema.id, identifier_id=ii.id)
    sid_f = LocationSchemaIdentifierRelation(schema_id=schema.id, identifier_id=fi.id)
    sid_b = LocationSchemaIdentifierRelation(schema_id=schema.id, identifier_id=bi.id)
    session.add(sid_s)
    session.add(sid_i)
    session.add(sid_f)
    session.add(sid_b)
    session.commit()
    assert isinstance(sid_s.id, int)
    assert isinstance(sid_i.id, int)
    assert isinstance(sid_f.id, int)
    assert isinstance(sid_b.id, int)
    loc = Location(schema_id=schema.id)
    session.add(loc)
    session.commit()
    assert isinstance(loc.id, int)

    zone = LocationStringValue(value="Zone A", identifier_id=si.id, location_id=loc.id)
    aisle = LocationIntegerValue(value=23, identifier_id=ii.id, location_id=loc.id)
    distance = LocationFloatValue(value=3.1, identifier_id=fi.id, location_id=loc.id)
    shelf = LocationBooleanValue(value=True, identifier_id=bi.id, location_id=loc.id)
    session.add(zone)
    session.add(aisle)
    session.add(distance)
    session.add(shelf)
    session.commit()
    assert isinstance(zone.id, int)
    assert isinstance(aisle.id, int)
    assert isinstance(distance.id, int)
    assert isinstance(shelf.id, int)
    session.close()


def test_add_xyz_location(session):
    x = LocationIdentifier(name="x", units="m", datatype="float")
    y = LocationIdentifier(name="y", units="m", datatype="float")
    z = LocationIdentifier(name="z", units="m", datatype="float")
    session.add(x)
    session.add(y)
    session.add(z)

    schema = LocationSchema(name="xyz")
    session.add(schema)
    session.flush()

    x_sid = LocationSchemaIdentifierRelation(schema_id=schema.id, identifier_id=x.id)
    y_sid = LocationSchemaIdentifierRelation(schema_id=schema.id, identifier_id=y.id)
    z_sid = LocationSchemaIdentifierRelation(schema_id=schema.id, identifier_id=z.id)
    session.add(x_sid)
    session.add(y_sid)
    session.add(z_sid)
    session.commit()

    loc = Location(schema_id=schema.id)
    session.add(loc)
    session.commit()
    xval = LocationFloatValue(value=2.0, identifier_id=x.id, location_id=loc.id)
    yval = LocationFloatValue(value=3.0, identifier_id=y.id, location_id=loc.id)
    zval = LocationFloatValue(value=4.0, identifier_id=z.id, location_id=loc.id)
    session.add(xval)
    session.add(yval)
    session.add(zval)
    session.commit()
    # see if we can retrieve the x,y,z values from the location
    coords = loc.float_values_relationship
    assert coords[0].value == 2.0
    assert coords[1].value == 3.0
    assert coords[2].value == 4.0
    session.close()
