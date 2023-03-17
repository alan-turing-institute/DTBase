"""
Test the functions for accessing the locations tables.
"""
import sqlalchemy as sqla
import pytest

from dtbase.core import locations


# Some constants we will use in the tests repeatedly.
LATITUDE1 = -2.0
LATITUDE2 = 12.3
LONGITUDE1 = 23.5
LONGITUDE2 = -0.0

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Functions for inserting some data into the database. These will called at the
# beginning of many tests to populate the database with data to test against. They are a
# lot like fixtures, but aren't fixtures because running them successfully is a test in
# itself.


def insert_identifiers(session):
    """Insert some location identifiers into the database."""
    locations.insert_location_identifier(
        name="latitude", units="", datatype="float", session=session
    )
    locations.insert_location_identifier(
        name="longitude", units="", datatype="float", session=session
    )


def insert_schemas(session):
    """Insert a location schema into the database."""
    insert_identifiers(session)
    locations.insert_location_schema(
        name="latlong",
        description="Latitude and longitude",
        identifiers=["latitude", "longitude"],
        session=session,
    )
    locations.insert_location_schema(
        name="lat only",
        description="Latitude only",
        identifiers=["latitude"],
        session=session,
    )


def insert_locations(session):
    """Insert some locations into the database."""
    insert_schemas(session)
    locations.insert_location(
        "latlong", latitude=LATITUDE1, longitude=LONGITUDE1, session=session
    )
    locations.insert_location(
        "latlong", latitude=LATITUDE2, longitude=LONGITUDE2, session=session
    )


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Tests for location identifiers


def test_insert_location_identifier(rollback_session):
    """Test inserting location identifiers."""
    insert_identifiers(rollback_session)


def test_insert_location_identifier_duplicate(rollback_session):
    """Try to insert a location identifier that conflicts with one that exists."""
    locations.insert_location_identifier(
        name="latitude", units="", datatype="float", session=rollback_session
    )
    error_msg = (
        "duplicate key value violates unique constraint "
        '"location_identifier_name_units_key"'
    )
    with pytest.raises(sqla.exc.IntegrityError, match=error_msg):
        locations.insert_location_identifier(
            name="latitude", units="", datatype="integer", session=rollback_session
        )


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Tests for location schemas


def test_insert_location_schema(rollback_session):
    """Test inserting a location schema."""
    insert_schemas(rollback_session)


def test_insert_location_schema_duplicate(rollback_session):
    """Try to insert a location schema that conflicts with one that exists."""
    insert_schemas(rollback_session)
    error_msg = (
        'duplicate key value violates unique constraint "location_schema_name_key"'
    )
    with pytest.raises(sqla.exc.IntegrityError, match=error_msg):
        locations.insert_location_schema(
            name="latlong",
            description="Latimer and Longchamp",
            identifiers=["latitude", "longitude"],
            session=rollback_session,
        )


def test_insert_location_schema_no_identifierr(rollback_session):
    """Try to insert a location schema that uses identifiers that don't exist."""
    insert_schemas(rollback_session)
    error_msg = "No location identifier 'longitude_misspelled'"
    with pytest.raises(ValueError, match=error_msg):
        locations.insert_location_schema(
            name="latlong_misspelled",
            description="Latitude and longitude misspelled",
            identifiers=["latitude", "longitude_misspelled"],
            session=rollback_session,
        )


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Tests for locations


def test_insert_location(rollback_session):
    """Test inserting locations."""
    insert_locations(rollback_session)


def test_insert_location_duplicate(rollback_session):
    """Try to insert a location that already exists."""
    insert_locations(rollback_session)
    error_msg = (
        "Location with schema 'latlong' and coordinates "
        f"{{'latitude': {LATITUDE1}, 'longitude': {LONGITUDE1}}} already exists."
    )
    with pytest.raises(ValueError, match=error_msg):
        locations.insert_location(
            "latlong",
            latitude=LATITUDE1,
            longitude=LONGITUDE1,
            session=rollback_session,
        )


def test_insert_location_no_schema(rollback_session):
    """Try to insert a location with a non-existing schema."""
    insert_schemas(rollback_session)
    with pytest.raises(ValueError, match="No location schema 'heightitude'"):
        locations.insert_location(
            "heightitude", latitude=12.0, longitude=0.0, session=rollback_session
        )


def test_insert_location_wrong_identifier(rollback_session):
    """Try to insert a location with the wrong identifier."""
    insert_schemas(rollback_session)
    # The (|) or clauses are needed because order isn't guaranteed.
    error_msg = (
        "For schema latlong expected to receive location identifiers "
        "{'(latitude|longitude)', '(latitude|longitude)'} but got "
        "{'(height|longitude)', '(height|longitude)'}."
    )
    with pytest.raises(ValueError, match=error_msg):
        locations.insert_location(
            "latlong", height=12.0, longitude=0.0, session=rollback_session
        )


def test_insert_location_wrong_data_type(rollback_session):
    """Try to insert a location with the wrong datatype."""
    insert_schemas(rollback_session)
    error_msg = (
        "For location identifier 'latitude' expected a value of type float but "
        "got a <class 'str'>."
    )
    with pytest.raises(ValueError, match=error_msg):
        locations.insert_location(
            "latlong",
            latitude="this is a string",
            longitude=0.0,
            session=rollback_session,
        )


def test_list_locations(rollback_session):
    """Find the inserted locations."""
    insert_locations(rollback_session)
    all_locations = locations.list_locations("latlong", session=rollback_session)
    assert len(all_locations) == 2
    assert all_locations[0]["latitude"] == LATITUDE1
    assert all_locations[0]["longitude"] == LONGITUDE1
    assert all_locations[1]["latitude"] == LATITUDE2
    assert all_locations[1]["longitude"] == LONGITUDE2
    some_locations = locations.list_locations(
        "latlong", session=rollback_session, latitude=LATITUDE1
    )
    assert len(some_locations) == 1
    assert some_locations[0]["latitude"] == LATITUDE1
    assert some_locations[0]["longitude"] == LONGITUDE1
    no_locations = locations.list_locations(
        "latlong", session=rollback_session, latitude=-3.0
    )
    assert len(no_locations) == 0


def test_delete_location_identifier(rollback_session):
    """Delete a location identifier, check that it is deleted and can't be redeleted."""
    insert_identifiers(rollback_session)
    locations.delete_location_identifier("latitude", session=rollback_session)
    all_identifiers = locations.list_location_identifiers(session=rollback_session)
    assert len(all_identifiers) == 1

    # Doing the same deletion again should fail, since that row is gone.
    error_msg = "No location identifier 'latitude'"
    with pytest.raises(ValueError, match=error_msg):
        locations.delete_location_identifier("latitude", session=rollback_session)


def test_delete_location_identifier_schema_exists(rollback_session):
    """Try to delete a location identifier for which a location schema exists."""
    insert_schemas(rollback_session)
    error_msg = (
        'update or delete on table "location_identifier" violates foreign key constraint '
        '"location_schema_identifier_relation_identifier_id_fkey" on table '
        '"location_schema_identifier_relation"'
    )
    with pytest.raises(sqla.exc.IntegrityError, match=error_msg):
        locations.delete_location_identifier("latitude", session=rollback_session)


def test_delete_location_schema(rollback_session):
    """Delete a location schema, and check that it is deleted and can't be redeleted."""
    insert_schemas(rollback_session)
    locations.delete_location_schema("latlong", session=rollback_session)
    all_schemas = locations.list_location_schemas(session=rollback_session)
    assert len(all_schemas) == 1

    # Doing the same deletion again should fail, since that row is gone.
    error_msg = "No location schema 'latlong'"
    with pytest.raises(ValueError, match=error_msg):
        locations.delete_location_schema("latlong", session=rollback_session)


def test_delete_location_schema_location_exists(rollback_session):
    """Try to delete a location schema for which a location exists."""
    insert_locations(rollback_session)
    error_msg = (
        'update or delete on table "location_schema" violates foreign key '
        'constraint "location_schema_id_fkey" on table "location"'
    )
    with pytest.raises(sqla.exc.IntegrityError, match=error_msg):
        locations.delete_location_schema("latlong", session=rollback_session)


def test_delete_location(rollback_session):
    """Delete a location, and check that it is deleted and can't be redeleted."""
    insert_locations(rollback_session)
    locations.delete_location_by_coordinates(
        "latlong", latitude=LATITUDE2, longitude=LONGITUDE2, session=rollback_session
    )
    all_locations = locations.list_locations("latlong", session=rollback_session)
    assert len(all_locations) == 1

    # Doing the same deletion again should fail, since that row is gone.
    error_msg = (
        "Location not found: latlong, "
        f"{{'latitude': {LATITUDE2}, 'longitude': {LONGITUDE2}}}"
    )
    with pytest.raises(ValueError, match=error_msg):
        locations.delete_location_by_coordinates(
            "latlong",
            latitude=LATITUDE2,
            longitude=LONGITUDE2,
            session=rollback_session,
        )

    locations.delete_location_by_coordinates(
        "latlong", latitude=LATITUDE1, longitude=LONGITUDE1, session=rollback_session
    )
    all_locations = locations.list_locations("latlong", session=rollback_session)
    assert len(all_locations) == 0


def test_delete_location_nonexistent(rollback_session):
    """Try to delete a non-existent location."""
    insert_locations(rollback_session)
    error_msg = "Location not found: latlong, {'latitude': 0.0, 'longitude': 0.0}"
    with pytest.raises(ValueError, match=error_msg):
        locations.delete_location_by_coordinates(
            "latlong", latitude=0.0, longitude=0.0, session=rollback_session
        )
