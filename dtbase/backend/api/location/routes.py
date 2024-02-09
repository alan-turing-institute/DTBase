"""
Module (routes.py) to handle API endpoints related to Locations
"""
import logging

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from dtbase.backend.auth import authenticate_access
from dtbase.backend.models import (
    Coordinates,
    LocationIdentifier,
    LocationSchema,
    LocationSchemaIdentifier,
    MessageResponse,
    ValueTypes,
)
from dtbase.backend.utils import db_session
from dtbase.core import locations
from dtbase.core.exc import RowExistsError, RowMissingError

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/location", tags=["location"], dependencies=[Depends(authenticate_access)]
)


@router.post("/insert-location-schema", status_code=status.HTTP_201_CREATED)
def insert_location_schema(
    location_schema: LocationSchema, session: Session = Depends(db_session)
) -> MessageResponse:
    """
    Add a location schema to the database.
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


class InsertLocationData(BaseModel):
    identifiers: list[LocationIdentifier]
    values: list[ValueTypes]


@router.post("/insert-location", status_code=status.HTTP_201_CREATED)
def insert_location(
    location_data: InsertLocationData, session: Session = Depends(db_session)
) -> MessageResponse:
    """
    Add a location to the database, defining the schema at the same time.
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
    return MessageResponse(detail="Location inserted")


class InsertLocationDataExistingSchema(BaseModel):
    schema_name: str
    coordinates: Coordinates


@router.post("/insert-location-for-schema", status_code=status.HTTP_201_CREATED)
def insert_location_existing_schema(
    payload: InsertLocationDataExistingSchema, session: Session = Depends(db_session)
) -> MessageResponse:
    """
    Add a location to the database, given an existing schema name.
    POST request should have json data (mimetype "application/json")
    containing
    {
      "schema_name": <schema_name:str>,
      "identifier1_name": "value1",
       ...
    }
    with an identifier name and value for every identifier in the schema

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


@router.post("/list-locations", status_code=status.HTTP_200_OK)
def list_locations(
    payload: dict = Body(), session: Session = Depends(db_session)
) -> list[Coordinates]:
    """
    List location in the database, filtered by schema name.
    Optionally also filter by coordinates, if given identifiers in the payload.
    Payload should be of the form:
    {
      "schema_name": <schema_name:str>,
      "identifier1_name": <value1:float|int|str|bool>,
       ...
    }

    Returns results in the form:
    [
     { <identifier1:str>: <value1:str>, ...}, ...
    ]
    """
    if "schema_name" not in payload:
        raise HTTPException(status_code=400, detail="Schema name not provided")
    result = locations.list_locations(**payload, session=session)
    return [Coordinates(**r) for r in result]


@router.get("/list-location-schemas", status_code=status.HTTP_200_OK)
def list_location_schemas(
    session: Session = Depends(db_session),
) -> list[LocationSchema]:
    """
    List location schemas in the database.

    Returns results in the form:
    [
      {
       "name": <name:str>,
       "description": <description:str>,
       "identifiers": [
          {
            "name": <identifier_name:str>,
            "units": <units:str>,
            "datatype":<"float"|"integer"|"string"|"boolean">
           }, ...
       ]
      }
    ]
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


@router.post("/get-schema-details", status_code=status.HTTP_200_OK)
def get_schema_details(
    schema_identifier: LocationSchemaIdentifier, session: Session = Depends(db_session)
) -> LocationSchema:
    """
    Get a location schema and its identifiers from the database.
    """
    try:
        result = locations.get_schema_details(
            schema_identifier.schema_name, session=session
        )
    except RowMissingError:
        raise HTTPException(status_code=400, detail="No such schema")
    return LocationSchema(**result)


@router.post("/delete-location-schema", status_code=status.HTTP_200_OK)
def delete_location_schema(
    schema_identifier: LocationSchemaIdentifier, session: Session = Depends(db_session)
) -> MessageResponse:
    """
    Delete a location schema from the database.
    Payload should have the form:
    {'schema_name': <schema_name:str>}

    """
    schema_name = schema_identifier.schema_name
    try:
        locations.delete_location_schema(schema_name=schema_name, session=session)
        session.commit()
        return MessageResponse(
            detail=f"Location schema '{schema_name}' has been deleted."
        )
    except RowMissingError:
        raise HTTPException(
            status_code=400, detail=f"Location schema '{schema_name}' not found."
        )


class DeleteLocationData(BaseModel):
    schema_name: str
    coordinates: Coordinates


@router.post("/delete-location", status_code=status.HTTP_200_OK)
def delete_location(
    payload: DeleteLocationData, session: Session = Depends(db_session)
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
