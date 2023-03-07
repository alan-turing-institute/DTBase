"""
Test the functions for accessing the locations tables.
"""
import pytest

from dtbase.backend import locations


def test_insert_delete_locations(session):
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
    locations.insert_location("latlong", latitude=23.2, longitude=-5.3, session=session)
    session.commit()

    # Try to delete a non-existent location
    with pytest.raises(
        ValueError, match="Location not found: {'latitude': 0.0, 'longitude': 0.0}"
    ):
        locations.delete_location_by_coordinates(
            "latlong", latitude=0.0, longitude=0.0, session=session
        )
    # Delete the newly created location
    locations.delete_location_by_coordinates(
        "latlong", latitude=23.2, longitude=-5.3, session=session
    )
    with pytest.raises(
        ValueError, match="Location not found: {'latitude': 23.2, 'longitude': -5.3}"
    ):
        # Doing the same deletion again should fail, since that row is gone.
        locations.delete_location_by_coordinates(
            "latlong", latitude=23.2, longitude=-5.3, session=session
        )
    locations.delete_location_by_coordinates(
        "latlong", latitude=-2.0, longitude=10.4, session=session
    )
