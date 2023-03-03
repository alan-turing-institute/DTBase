"""
Test the functions for accessing the locations tables.
"""

from dtbase.backend import locations


def test_insert_locations(session):
    locations.insert_location_identifier(
        name="latitude", units="", datatype="float", session=session
    )
    locations.insert_location_identifier(
        name="longitude", units="", datatype="float", session=session
    )
    locations.insert_location_schema(
        name="latlong",
        description="Latitude and longitude",
        identifiers=["latitude", "longitude"],
        session=session,
    )
    locations.insert_location("latlong", latitude=-2.0, longitude=10.4, session=session)
