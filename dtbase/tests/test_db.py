"""
Test the basic structure of the database, creating rows and relations via
the SQLAlchemy ORM.
"""

from dtbase.core.structure import (
    Location,
    LocationIdentifier,
    LocationFloatValue,
    LocationIntegerValue,
    LocationStringValue,
    LocationBooleanValue,
)


def test_add_location_empty(session):
    loc = Location()
    session.add(loc)
    session.commit()
    assert isinstance(loc.id, int)
    session.close()


def test_add_location_identifiers(session):
    si = LocationIdentifier(name="zone", datatype="string")
    ii = LocationIdentifier(name="aisle", datatype="integer")
    fi = LocationIdentifier(name="distance", units="m", datatype="float")
    session.add(si)
    session.add(ii)
    session.add(fi)
    session.commit()
    assert isinstance(si.id, int)
    assert isinstance(ii.id, int)
    assert isinstance(fi.id, int)
    session.close()


def test_add_xyz_location(session):
    loc = Location()
    x = LocationIdentifier(name="x", units="m", datatype="float")
    y = LocationIdentifier(name="y", units="m", datatype="float")
    z = LocationIdentifier(name="z", units="m", datatype="float")
    session.add(loc)
    session.add(x)
    session.add(y)
    session.add(z)
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
