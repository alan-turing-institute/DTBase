"""
Test the functions for accessing the locations tables.
"""
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from dtbase.backend.database import locations
from dtbase.backend.exc import RowExistsError, RowMissingError

# Some constants we will use in the tests repeatedly.
LATITUDE1 = -2.0
LATITUDE2 = 12.3
LONGITUDE1 = 23.5
LONGITUDE2 = -0.0
LATITUDE3 = 144.0

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Functions for inserting some data into the database. These will called at the
# beginning of many tests to populate the database with data to test against. They are a
# lot like fixtures, but aren't fixtures because running them successfully is a test in
# itself.


def insert_identifiers(session: Session) -> None:
    """Insert some location identifiers into the database."""
    locations.insert_location_identifier(
        name="latitude", units="", datatype="float", session=session
    )
    locations.insert_location_identifier(
        name="longitude", units="", datatype="float", session=session
    )


def insert_schemas(session: Session) -> None:
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


def insert_locations(session: Session) -> None:
    """Insert some locations into the database."""
    insert_schemas(session)
    locations.insert_location(
        "latlong",
        coordinates={"latitude": LATITUDE1, "longitude": LONGITUDE1},
        session=session,
    )
    locations.insert_location(
        "latlong",
        coordinates={"latitude": LATITUDE2, "longitude": LONGITUDE2},
        session=session,
    )
    locations.insert_location(
        "lat only", coordinates={"latitude": LATITUDE3}, session=session
    )


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Tests for location identifiers


def test_insert_location_identifier(session: Session) -> None:
    """Test inserting location identifiers."""
    insert_identifiers(session)


def test_insert_location_identifier_duplicate(session: Session) -> None:
    """Try to insert a location identifier that conflicts with one that exists."""
    locations.insert_location_identifier(
        name="latitude", units="", datatype="float", session=session
    )
    original_identifiers = locations.list_location_identifiers(session=session)

    # Try to insert a duplicate location identifier.
    locations.insert_location_identifier(
        name="latitude", units="", datatype="integer", session=session
    )

    new_identifiers = locations.list_location_identifiers(session=session)
    # Verify that the list hasn't changed.
    assert (
        original_identifiers == new_identifiers
    ), "Inserting a duplicate altered the location identifiers"


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Tests for location schemas


def test_insert_location_schema(session: Session) -> None:
    """Test inserting a location schema."""
    insert_schemas(session)


def test_insert_location_schema_duplicate(session: Session) -> None:
    """Try to insert a location schema that conflicts with one that exists."""
    insert_schemas(session)
    error_msg = (
        'duplicate key value violates unique constraint "location_schema_name_key"'
    )
    with pytest.raises(IntegrityError, match=error_msg):
        locations.insert_location_schema(
            name="latlong",
            description="Latimer and Longchamp",
            identifiers=["latitude", "longitude"],
            session=session,
        )


def test_insert_location_schema_no_identifierr(session: Session) -> None:
    """Try to insert a location schema that uses identifiers that don't exist."""
    insert_schemas(session)
    error_msg = "No location identifier 'longitude_misspelled'"
    with pytest.raises(RowMissingError, match=error_msg):
        locations.insert_location_schema(
            name="latlong_misspelled",
            description="Latitude and longitude misspelled",
            identifiers=["latitude", "longitude_misspelled"],
            session=session,
        )


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Tests for locations


def test_insert_location(session: Session) -> None:
    """Test inserting locations."""
    insert_locations(session)


def test_insert_location_duplicate(session: Session) -> None:
    """Try to insert a location that already exists."""
    insert_locations(session)
    error_msg = (
        "Location with schema 'latlong' and coordinates "
        f"{{'latitude': {LATITUDE1}, 'longitude': {LONGITUDE1}}} already exists."
    )
    with pytest.raises(RowExistsError, match=error_msg):
        locations.insert_location(
            "latlong",
            coordinates={"latitude": LATITUDE1, "longitude": LONGITUDE1},
            session=session,
        )


def test_insert_location_no_schema(session: Session) -> None:
    """Try to insert a location with a non-existing schema."""
    insert_schemas(session)
    with pytest.raises(RowMissingError, match="No location schema 'heightitude'"):
        locations.insert_location(
            "heightitude",
            coordinates={"latitude": 12.0, "longitude": 0.0},
            session=session,
        )


def test_insert_location_wrong_identifier(session: Session) -> None:
    """Try to insert a location with the wrong identifier."""
    insert_schemas(session)
    # The (|) or clauses are needed because order isn't guaranteed.
    error_msg = (
        "For schema latlong expected to receive location identifiers "
        "{'(latitude|longitude)', '(latitude|longitude)'} but got "
        "{'(height|longitude)', '(height|longitude)'}."
    )
    with pytest.raises(ValueError, match=error_msg):
        locations.insert_location(
            "latlong", coordinates={"height": 12.0, "longitude": 0.0}, session=session
        )


def test_insert_location_wrong_data_type(session: Session) -> None:
    """Try to insert a location with the wrong datatype."""
    insert_schemas(session)
    error_msg = (
        "For location identifier 'latitude' expected a value of type float but "
        "got a <class 'str'>."
    )
    with pytest.raises(ValueError, match=error_msg):
        locations.insert_location(
            "latlong",
            coordinates={"latitude": "this is a string", "longitude": 0.0},
            session=session,
        )


def test_list_locations(session: Session) -> None:
    """Find the inserted locations."""
    insert_locations(session)
    all_locations = locations.list_locations("latlong", session=session)
    assert len(all_locations) == 2
    assert all_locations[0]["latitude"] == LATITUDE1
    assert all_locations[0]["longitude"] == LONGITUDE1
    assert all_locations[1]["latitude"] == LATITUDE2
    assert all_locations[1]["longitude"] == LONGITUDE2
    some_locations = locations.list_locations(
        "latlong", session=session, coordinates={"latitude": LATITUDE1}
    )
    assert len(some_locations) == 1
    assert some_locations[0]["latitude"] == LATITUDE1
    assert some_locations[0]["longitude"] == LONGITUDE1
    no_locations = locations.list_locations(
        "latlong", session=session, coordinates={"latitude": -3.0}
    )
    assert len(no_locations) == 0


def test_delete_location_identifier(session: Session) -> None:
    """Delete a location identifier, check that it is deleted and can't be redeleted."""
    insert_identifiers(session)
    locations.delete_location_identifier("latitude", session=session)
    all_identifiers = locations.list_location_identifiers(session=session)
    assert len(all_identifiers) == 1

    # Doing the same deletion again should fail, since that row is gone.
    error_msg = "No location identifier 'latitude'"
    with pytest.raises(RowMissingError, match=error_msg):
        locations.delete_location_identifier("latitude", session=session)


def test_delete_location_identifier_schema_exists(session: Session) -> None:
    """Try to delete a location identifier for which a location schema exists."""
    insert_schemas(session)
    error_msg = (
        'update or delete on table "location_identifier" violates foreign key '
        'constraint "location_schema_identifier_relation_identifier_id_fkey" on table '
        '"location_schema_identifier_relation"'
    )
    with pytest.raises(IntegrityError, match=error_msg):
        locations.delete_location_identifier("latitude", session=session)


def test_delete_location_schema(session: Session) -> None:
    """Delete a location schema, and check that it is deleted and can't be redeleted."""
    insert_schemas(session)
    locations.delete_location_schema("latlong", session=session)
    all_schemas = locations.list_location_schemas(session=session)
    assert len(all_schemas) == 1

    # Doing the same deletion again should fail, since that row is gone.
    error_msg = "No location schema 'latlong'"
    with pytest.raises(RowMissingError, match=error_msg):
        locations.delete_location_schema("latlong", session=session)


def test_delete_location_schema_location_exists(session: Session) -> None:
    """Try to delete a location schema for which a location exists."""
    insert_locations(session)
    error_msg = (
        'update or delete on table "location_schema" violates foreign key '
        'constraint "location_schema_id_fkey" on table "location"'
    )
    with pytest.raises(IntegrityError, match=error_msg):
        locations.delete_location_schema("latlong", session=session)


def test_delete_location(session: Session) -> None:
    """Delete a location, and check that it is deleted and can't be redeleted."""
    insert_locations(session)
    locations.delete_location_by_coordinates(
        "latlong",
        coordinates={"latitude": LATITUDE2, "longitude": LONGITUDE2},
        session=session,
    )
    all_locations = locations.list_locations("latlong", session=session)
    assert len(all_locations) == 1

    # Doing the same deletion again should fail, since that row is gone.
    error_msg = (
        "Location not found: latlong, "
        f"{{'latitude': {LATITUDE2}, 'longitude': {LONGITUDE2}}}"
    )
    with pytest.raises(RowMissingError, match=error_msg):
        locations.delete_location_by_coordinates(
            "latlong",
            coordinates={"latitude": LATITUDE2, "longitude": LONGITUDE2},
            session=session,
        )

    locations.delete_location_by_coordinates(
        "latlong",
        coordinates={"latitude": LATITUDE1, "longitude": LONGITUDE1},
        session=session,
    )
    all_locations = locations.list_locations("latlong", session=session)
    assert len(all_locations) == 0


def test_delete_location_nonexistent(session: Session) -> None:
    """Try to delete a non-existent location."""
    insert_locations(session)
    error_msg = "Location not found: latlong, {'latitude': 0.0, 'longitude': 0.0}"
    with pytest.raises(RowMissingError, match=error_msg):
        locations.delete_location_by_coordinates(
            "latlong", coordinates={"latitude": 0.0, "longitude": 0.0}, session=session
        )
