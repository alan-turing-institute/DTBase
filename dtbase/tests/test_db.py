"""
Test the basic structure of the database, creating rows and relations via
the SQLAlchemy ORM.
"""

from dtbase.core.structure import (
    LocationClass,
    LocationStringIdentifierClass,
    LocationIntegerIdentifierClass,
    LocationFloatIdentifierClass,
    LocationStringValueClass,
    LocationIntegerValueClass,
    LocationFloatValueClass,
)


def test_add_location_empty(session):
    loc = LocationClass()
    session.add(loc)
    session.commit()
    assert isinstance(loc.id, int)
    session.close()


def test_add_location_identifiers(session):
    si = LocationStringIdentifierClass(name="zone")
    ii = LocationIntegerIdentifierClass(name="aisle")
    fi = LocationFloatIdentifierClass(name="distance", units="m")
    session.add(si)
    session.add(ii)
    session.add(fi)
    session.commit()
    assert isinstance(si.id, int)
    assert isinstance(ii.id, int)
    assert isinstance(fi.id, int)
    session.close()


def test_add_xyz_location(session):
    loc = LocationClass()
    x = LocationFloatIdentifierClass(name="x", units="m")
    y = LocationFloatIdentifierClass(name="y", units="m")
    z = LocationFloatIdentifierClass(name="z", units="m")
    session.add(loc)
    session.add(x)
    session.add(y)
    session.add(z)
    session.commit()
    xval = LocationFloatValueClass(value=2.0, variable_id=x.id, location_id=loc.id)
    yval = LocationFloatValueClass(value=3.0, variable_id=y.id, location_id=loc.id)
    zval = LocationFloatValueClass(value=4.0, variable_id=z.id, location_id=loc.id)
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
