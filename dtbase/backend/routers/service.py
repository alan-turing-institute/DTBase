"""
Module (routes.py) to handle API endpoints related to service management
"""
import datetime as dt
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from dtbase.backend.auth import authenticate_access
from dtbase.backend.database import service
from dtbase.backend.database.utils import db_session
from dtbase.backend.models import MessageResponse
from dtbase.core.exc import RowExistsError, RowMissingError

router = APIRouter(
    prefix="/service",
    tags=["service"],
    dependencies=[Depends(authenticate_access)],
    responses={status.HTTP_401_UNAUTHORIZED: {"model": MessageResponse}},
)


class Service(BaseModel):
    name: str
    url: str
    http_method: str


@router.post(
    "/insert-service",
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: {"model": MessageResponse}},
)
def insert_service(
    payload: Service, session: Session = Depends(db_session)
) -> MessageResponse:
    """Create a new service."""
    try:
        service.insert_service(session=session, **payload.model_dump())
        session.commit()
    except RowExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Service already exists.",
        )
    return MessageResponse(detail="Service created successfully.")


@router.get("/list-services", status_code=status.HTTP_200_OK)
def list_services(session: Session = Depends(db_session)) -> list[Service]:
    """List all services."""
    services = service.list_services(session=session)
    return [Service(**s) for s in services]


class DeleteServiceRequest(BaseModel):
    name: str


@router.post(
    "/delete-service",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_400_BAD_REQUEST: {"model": MessageResponse}},
)
def delete_service(
    payload: DeleteServiceRequest, session: Session = Depends(db_session)
) -> MessageResponse:
    """Delete a service."""
    try:
        service.delete_service(session=session, service_name=payload.name)
        session.commit()
    except RowMissingError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Service does not exist.",
        )
    return MessageResponse(detail="Service deleted successfully.")


class InsertParameterSetRequest(BaseModel):
    service_name: str
    name: str
    parameters: dict


@router.post(
    "/insert-parameter-set",
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: {"model": MessageResponse}},
)
def insert_parameter_set(
    payload: InsertParameterSetRequest, session: Session = Depends(db_session)
) -> MessageResponse:
    """Insert a named parameter set for a service."""
    try:
        service.insert_parameter_set(session=session, **payload.model_dump())
        session.commit()
    except RowExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Parameter set already exists.",
        )
    return MessageResponse(detail="Parameter set created successfully.")


class DeleteParameterSetRequest(BaseModel):
    service_name: str
    name: str


@router.post(
    "/delete-parameter-set",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_400_BAD_REQUEST: {"model": MessageResponse}},
)
def delete_parameter_set(
    payload: DeleteParameterSetRequest, session: Session = Depends(db_session)
) -> MessageResponse:
    """Delete a named parameter set."""
    try:
        service.delete_parameter_set(session=session, **payload.model_dump())
        session.commit()
    except RowMissingError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parameter set does not exist.",
        )
    return MessageResponse(detail="Parameter set deleted successfully.")


class ListParameterSetsRequest(BaseModel):
    service_name: Optional[str] = Field(None)


class ParameterSet(BaseModel):
    service_name: str
    name: str
    parameters: dict


@router.post("/list-parameter-sets", status_code=status.HTTP_200_OK)
def list_parameter_sets(
    payload: Optional[ListParameterSetsRequest] = None,
    session: Session = Depends(db_session),
) -> list[ParameterSet]:
    """List all parameter sets.

    Optionally filter by service name.
    """
    if payload is None:
        payload = ListParameterSetsRequest(service_name=None)
    parameter_sets = service.list_parameter_sets(
        session=session, **payload.model_dump()
    )
    return [ParameterSet(**p) for p in parameter_sets]


class EditParameterSetRequest(BaseModel):
    service_name: str
    name: str
    parameters: dict


@router.post(
    "/edit-parameter-set",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_400_BAD_REQUEST: {"model": MessageResponse}},
)
def edit_parameter_set(
    payload: EditParameterSetRequest, session: Session = Depends(db_session)
) -> MessageResponse:
    """Edit a named parameter set for a service."""
    try:
        service.edit_parameter_set(session=session, **payload.model_dump())
        session.commit()
    except RowMissingError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parameter set does not exist.",
        )
    return MessageResponse(detail="Parameter set edited successfully.")


class CallServiceRequest(BaseModel):
    service_name: str
    parameter_set_name: Optional[str] = Field(None)
    parameters: Optional[dict | list] = Field(None)


@router.post(
    "/run-service",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_400_BAD_REQUEST: {"model": MessageResponse}},
)
def run_service(
    payload: CallServiceRequest, session: Session = Depends(db_session)
) -> MessageResponse:
    """Call a service.

    In addition to the name of the service to call, either a JSON object of parameters
    or the name of a named set of parameters must be provided. Providing both will
    return a 400 Bad Request error.
    """
    try:
        service.run_service(session=session, **payload.model_dump())
        session.commit()
    except RowMissingError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Service or parameter set does not exist.",
        )
    return MessageResponse(detail="Service called successfully.")


class ListServiceRunsRequest(BaseModel):
    service_name: Optional[str] = Field(None)
    parameter_set_name: Optional[str] = Field(None)


class ServiceRun(BaseModel):
    service_name: str
    parameter_set_name: Optional[str]
    parameters: Optional[dict]
    response_json: Optional[dict]
    response_status_code: int
    timestamp: dt.datetime


@router.post("/list-runs", status_code=status.HTTP_200_OK)
def list_runs(
    payload: Optional[ListServiceRunsRequest] = None,
    session: Session = Depends(db_session),
) -> list[ServiceRun]:
    """List all runs of a service.

    Filtering by service name and/or parameter set name is optional. Filtering by
    parameter set can only be done if a service name is provided.
    """
    if payload is None:
        payload = ListServiceRunsRequest(service_name=None, parameter_set_name=None)
    runs = service.list_runs(session=session, **payload.model_dump())
    return [ServiceRun(**r) for r in runs]
