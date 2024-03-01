"""
Module (routes.py) to handle API endpoints related to Locations
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from dtbase.backend.auth import authenticate_access
from dtbase.backend.database import locations
from dtbase.backend.database.utils import db_session
from dtbase.backend.models import (
    Coordinates,
    LocationIdentifier,
    LocationSchema,
    MessageResponse,
    ValueType,
)
from dtbase.core.exc import RowExistsError, RowMissingError

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/location",
    tags=["location"],
    dependencies=[Depends(authenticate_access)],
    responses={status.HTTP_401_UNAUTHORIZED: {"model": MessageResponse}},
)


@router.post(
    "/insert-location-schema",
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: {"model": MessageResponse}},
)
def insert_location_schema(
    location_schema: LocationSchema, session: Session = Depends(db_session)
) -> MessageResponse:
    """
    Add a location schema to the database.

    A location is defined by its name description and a list of location identifiers
    that are used to specify locations in this schema.

    For instance, a location schema might be "latitude-longitude" with identifiers
    "latitude" and "longitude", or "campus-room-numbering" with identifiers
    "building name", "floor", and "room".
    """
    idnames = []
    for identifier in location_schema.identifiers:
        locations.insert_location_identifier(
            name=identifier.name,
            units=identifier.units,
            datatype=identifier.datatype,
            session=session,
        )
        idnames.append(identifier.name)
    # sort the idnames list, and use it to create/find a schema
    idnames.sort()
    try:
        locations.insert_location_schema(
            name=location_schema.name,
            description=location_schema.description,
            identifiers=idnames,
            session=session,
        )
        session.commit()
    except IntegrityError:
        raise HTTPException(status_code=409, detail="LocationSchema exists already")
    return MessageResponse(detail="Location schema inserted")


class InsertLocationRequest(BaseModel):
    identifiers: list[LocationIdentifier]
    values: list[ValueType]


class InsertLocationResponse(BaseModel):
    schema_name: str


@router.post(
    "/insert-location",
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: {"model": MessageResponse}},
)
def insert_location(
    location_data: InsertLocationRequest, session: Session = Depends(db_session)
) -> InsertLocationResponse:
    """
    Add a location to the database, defining the schema at the same time.

    There should be as many values in the "values" list as there are identifiers in the
    "identifiers" list. The order of the values should correspond to the order of the
    identifiers, and the datatypes should match.
    """
    try:
        idnames = []
        for identifier in location_data.identifiers:
            locations.insert_location_identifier(
                name=identifier.name,
                units=identifier.units,
                datatype=identifier.datatype,
                session=session,
            )
            idnames.append(identifier.name)
        # sort the idnames list, and use it to create/find a schema
        idnames.sort()
        schema_name = "-".join(idnames)
        locations.insert_location_schema(
            name=schema_name,
            description=schema_name,
            identifiers=idnames,
            session=session,
        )
        coordinates = {}
        for i, val in enumerate(location_data.values):
            coordinates[location_data.identifiers[i].name] = val
        locations.insert_location(schema_name, coordinates, session=session)
        session.commit()
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Location or schema exists already")
    return InsertLocationResponse(schema_name=schema_name)


class InsertLocationForExistingSchemaRequest(BaseModel):
    schema_name: str
    coordinates: Coordinates


@router.post(
    "/insert-location-for-schema",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {"model": MessageResponse},
        status.HTTP_400_BAD_REQUEST: {"model": MessageResponse},
    },
)
def insert_location_existing_schema(
    payload: InsertLocationForExistingSchemaRequest,
    session: Session = Depends(db_session),
) -> MessageResponse:
    """
    Add a location to the database, given an existing schema name.

    The keys of the coordinates should match the identifiers of the schema.
    """
    try:
        locations.insert_location(
            payload.schema_name, payload.coordinates.model_dump(), session=session
        )
        session.commit()
    except RowMissingError:
        raise HTTPException(status_code=400, detail="Location schema does not exist")
    except RowExistsError:
        raise HTTPException(status_code=409, detail="Location exists already")
    return MessageResponse(detail="Location inserted")


class ListLocationRequest(BaseModel):
    schema_name: str
    coordinates: Optional[Coordinates] = Field(default=None)


@router.post(
    "/list-locations",
    status_code=status.HTTP_200_OK,
)
def list_locations(
    payload: ListLocationRequest, session: Session = Depends(db_session)
) -> list[Coordinates]:
    """
    List location in the database, filtered by schema name.

    Optionally also filter by coordinates, if given identifiers in the payload.
    """
    result = locations.list_locations(**payload.model_dump(), session=session)
    return [Coordinates(**r) for r in result]


@router.get("/list-location-schemas", status_code=status.HTTP_200_OK)
def list_location_schemas(
    session: Session = Depends(db_session),
) -> list[LocationSchema]:
    """
    List location schemas in the database.
    """
    result = locations.list_location_schemas(session=session)
    return [LocationSchema(**r) for r in result]


@router.get("/list-location-identifiers", status_code=status.HTTP_200_OK)
def list_location_identifiers(
    session: Session = Depends(db_session),
) -> list[LocationIdentifier]:
    """
    List location identifiers in the database.
    """
    result = locations.list_location_identifiers(session=session)
    return [LocationIdentifier(**r) for r in result]


class GetSchemaDetailsRequest(BaseModel):
    schema_name: str


@router.post(
    "/get-schema-details",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_400_BAD_REQUEST: {"model": MessageResponse}},
)
def get_schema_details(
    payload: GetSchemaDetailsRequest, session: Session = Depends(db_session)
) -> LocationSchema:
    """
    Get a location schema and its identifiers from the database.
    """
    try:
        result = locations.get_schema_details(payload.schema_name, session=session)
    except RowMissingError:
        raise HTTPException(status_code=400, detail="No such schema")
    return LocationSchema(**result)


class DeleteLocationSchemaRequest(BaseModel):
    schema_name: str


@router.post(
    "/delete-location-schema",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_400_BAD_REQUEST: {"model": MessageResponse}},
)
def delete_location_schema(
    payload: DeleteLocationSchemaRequest, session: Session = Depends(db_session)
) -> MessageResponse:
    """
    Delete a location schema from the database.
    """
    schema_name = payload.schema_name
    try:
        locations.delete_location_schema(schema_name=schema_name, session=session)
        session.commit()
    except RowMissingError:
        raise HTTPException(
            status_code=400, detail=f"Location schema '{schema_name}' not found."
        )
    return MessageResponse(detail=f"Location schema '{schema_name}' has been deleted.")


class DeleteLocationRequest(BaseModel):
    schema_name: str
    coordinates: Coordinates


@router.post(
    "/delete-location",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_400_BAD_REQUEST: {"model": MessageResponse}},
)
def delete_location(
    payload: DeleteLocationRequest, session: Session = Depends(db_session)
) -> MessageResponse:
    """
    Delete a location with the specified schema name and coordinates.
    """
    try:
        locations.delete_location_by_coordinates(
            payload.schema_name, payload.coordinates.model_dump(), session=session
        )
        session.commit()
        return MessageResponse(detail="Location deleted")
    except RowMissingError:
        raise HTTPException(status_code=400, detail="Location not found")
