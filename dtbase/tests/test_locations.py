"""
Test the functions for accessing the locations tables.
"""
import sqlalchemy
import pytest

from dtbase.core import locations


def test_locations(session):
    """Test locations.

    Run a long list of tests for locations, creating identifiers, a schema,
    locations, listing them, deleting them, and trying a number of invalid function
    calls and checking that they raise errors as expected.
    """
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

    # Try to add a location identifier that conflicts with one that exists.
    with pytest.raises(
        sqlalchemy.exc.IntegrityError,
        match="duplicate key value violates unique constraint "
        '"location_identifier_name_units_key"',
    ):
        locations.insert_location_identifier(
            name="longitude", units="", datatype="integer", session=session
        )
    session.rollback()

    # Try to add a location schema that uses identifiers that don't exist.
    with pytest.raises(
        ValueError, match="No location identifier named longitude_misspelled"
    ):
        locations.insert_location_schema(
            name="latlong_misspelled",
            description="Latitude and longitude misspelled",
            identifiers=["latitude", "longitude_misspelled"],
            session=session,
        )
    # Try to add a location schema that conflicts with one that exists.
    with pytest.raises(
        sqlalchemy.exc.IntegrityError,
        match='duplicate key value violates unique constraint "location_schema_name_key"',
    ):
        locations.insert_location_schema(
            name="latlong",
            description="Latimer and Longchamp",
            identifiers=["latitude", "longitude"],
            session=session,
        )
    session.rollback()

    # Try to add a location that already exists.
    with pytest.raises(
        ValueError,
        match="Location with schema 'latlong' and coordinates "
        "{'latitude': -2.0, 'longitude': 10.4} already exists.",
    ):
        locations.insert_location(
            "latlong", latitude=-2.0, longitude=10.4, session=session
        )
    # Try to add a location with a non-existing schema
    with pytest.raises(
        ValueError,
        match="No location schema named heightitude",
    ):
        locations.insert_location(
            "heightitude", latitude=12.0, longitude=0.0, session=session
        )
    # Try to add a location with the wrong identifier
    with pytest.raises(
        ValueError,
        # The (|) or clauses are needed because order isn't guaranteed.
        match="For schema latlong expected to receive location identifiers "
        "{'(latitude|longitude)', '(latitude|longitude)'} but got "
        "{'(height|longitude)', '(height|longitude)'}.",
    ):
        locations.insert_location(
            "latlong", height=12.0, longitude=0.0, session=session
        )
    # Try to add a location with the wrong datatype
    with pytest.raises(
        ValueError,
        match="For location identifier 'latitude' expected a value of type float but "
        "got a <class 'str'>.",
    ):
        locations.insert_location(
            "latlong", latitude="this is a string", longitude=0.0, session=session
        )

    # Find the inserted locations
    all_locations = locations.list_locations("latlong", session=session)
    assert len(all_locations) == 2
    assert all_locations[0]["latitude"] == -2.0
    assert all_locations[0]["longitude"] == 10.4
    assert all_locations[1]["latitude"] == 23.2
    assert all_locations[1]["longitude"] == -5.3
    some_locations = locations.list_locations("latlong", session=session, latitude=-2.0)
    assert len(some_locations) == 1
    assert some_locations[0]["latitude"] == -2.0
    assert some_locations[0]["longitude"] == 10.4
    no_locations = locations.list_locations("latlong", session=session, latitude=-3.0)
    assert len(no_locations) == 0

    # Try to delete a non-existent location
    with pytest.raises(
        ValueError,
        match="Location not found: latlong, {'latitude': 0.0, 'longitude': 0.0}",
    ):
        locations.delete_location_by_coordinates(
            "latlong", latitude=0.0, longitude=0.0, session=session
        )

    # Delete the newly created location
    locations.delete_location_by_coordinates(
        "latlong", latitude=23.2, longitude=-5.3, session=session
    )
    all_locations = locations.list_locations("latlong", session=session)
    assert len(all_locations) == 1

    # Doing the same deletion again should fail, since that row is gone.
    with pytest.raises(
        ValueError,
        match="Location not found: latlong, {'latitude': 23.2, 'longitude': -5.3}",
    ):
        locations.delete_location_by_coordinates(
            "latlong", latitude=23.2, longitude=-5.3, session=session
        )
    locations.delete_location_by_coordinates(
        "latlong", latitude=-2.0, longitude=10.4, session=session
    )
    all_locations = locations.list_locations("latlong", session=session)
    assert len(all_locations) == 0

    session.close()
