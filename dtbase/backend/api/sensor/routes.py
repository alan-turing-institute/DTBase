"""
Module (routes.py) to handle API endpoints related to sensors
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, RootModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from dtbase.backend.auth import authenticate_access
from dtbase.backend.db import db_session
from dtbase.backend.models import MessageResponse, SensorMeasure, SensorType, ValueType
from dtbase.core import sensor_locations, sensors
from dtbase.core.exc import RowMissingError

router = APIRouter(
    prefix="/sensor",
    tags=["sensor"],
    dependencies=[Depends(authenticate_access)],
    responses={status.HTTP_401_UNAUTHORIZED: {"model": MessageResponse}},
)


@router.post(
    "/insert-sensor-type",
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: {"model": MessageResponse}},
)
def insert_sensor_type(
    payload: SensorType, session: Session = Depends(db_session)
) -> MessageResponse:
    """
    Add a sensor type to the database.
    """
    for measure in payload.measures:
        # TODO This loop might run into trouble if one of the measures exists already
        # but others don't, since the session.rollback() rolls them all back.
        # Note that we probably do want all of this to be rolled back if the sensor type
        # exists.
        try:
            sensors.insert_sensor_measure(
                name=measure.name,
                units=measure.units,
                datatype=measure.datatype,
                session=session,
            )
        except IntegrityError:
            # Sensor measure already exists.
            session.rollback()
    try:
        sensors.insert_sensor_type(
            name=payload.name,
            description=payload.description,
            measures=[m.model_dump() for m in payload.measures],
            session=session,
        )
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Sensor type exists already")
    return MessageResponse(detail="Sensor type inserted")


class InsertSensorRequest(BaseModel):
    type_name: str
    unique_identifier: str
    name: Optional[str] = Field(default=None)
    notes: Optional[str] = Field(default=None)


@router.post(
    "/insert-sensor",
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: {"model": MessageResponse}},
)
def insert_sensor(
    payload: InsertSensorRequest, session: Session = Depends(db_session)
) -> MessageResponse:
    """
    Add a sensor to the database.
    """
    try:
        sensors.insert_sensor(**payload.model_dump(), session=session)
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Sensor exists already")
    session.commit()
    return MessageResponse(detail="Sensor inserted")


class InsertSensorLocationRequest(BaseModel):
    unique_identifier: str
    schema_name: str
    coordinates: dict[str, ValueType]
    installation_datetime: datetime = Field(default_factory=datetime.now)


@router.post("/insert-sensor-location", status_code=status.HTTP_201_CREATED)
def insert_sensor_location(
    payload: InsertSensorLocationRequest, session: Session = Depends(db_session)
) -> MessageResponse:
    """
    Add a sensor location installation to the database.

    The `unique_identifier` field is the unique identifier of the sensor.
    """
    sensor_locations.insert_sensor_location(
        sensor_uniq_id=payload.unique_identifier,
        schema_name=payload.schema_name,
        coordinates=payload.coordinates,
        installation_datetime=payload.installation_datetime,
        session=session,
    )
    session.commit()
    return MessageResponse(detail="Sensor location inserted")


class ListSensorLocationsRequest(BaseModel):
    unique_identifier: str


LocationHistoryResponse = RootModel[dict[str, ValueType | datetime]]


@router.post("/list-sensor-locations", status_code=status.HTTP_200_OK)
def list_sensor_locations(
    payload: ListSensorLocationsRequest, session: Session = Depends(db_session)
) -> list[LocationHistoryResponse]:
    """
    Get the location history of a sensor.

    The elements in the return value will have the keys `installation_datetime`, and
    whatever location identifiers the relevant location schema has.
    """
    result = sensor_locations.get_location_history(
        sensor_uniq_id=payload.unique_identifier, session=session
    )
    return [LocationHistoryResponse(**entry) for entry in result]


class InsertSensorReadingsRequest(BaseModel):
    measure_name: str
    unique_identifier: str
    readings: list[ValueType]
    timestamps: list[datetime]


@router.post("/insert-sensor-readings", status_code=status.HTTP_201_CREATED)
def insert_sensor_readings(
    payload: InsertSensorReadingsRequest, session: Session = Depends(db_session)
) -> MessageResponse:
    """
    Add sensor readings to the database.

    The `unique_identifier` field is the unique identifier of the sensor. There should
    as mayn readings as there are timestamps.
    """
    sensors.insert_sensor_readings(
        measure_name=payload.measure_name,
        unique_identifier=payload.unique_identifier,
        readings=payload.readings,
        timestamps=payload.timestamps,
        session=session,
    )
    session.commit()
    return MessageResponse(detail="Sensor readings inserted")


class ListSensorsRequest(BaseModel):
    type_name: Optional[str] = Field(default=None)


class ListSensorsResponse(BaseModel):
    unique_identifier: str
    name: Optional[str] = Field(default=None)
    notes: Optional[str] = Field(default=None)


@router.post("/list-sensors", status_code=status.HTTP_200_OK)
def list_sensors(
    payload: ListSensorsRequest, session: Session = Depends(db_session)
) -> list[ListSensorsResponse]:
    """
    List sensors of a particular type in the database.
    """
    result = sensors.list_sensors(type_name=payload.type_name, session=session)
    return [ListSensorsResponse(**sensor) for sensor in result]


@router.get("/list-sensor-types", status_code=status.HTTP_200_OK)
def list_sensor_types(session: Session = Depends(db_session)) -> list[SensorType]:
    """
    List sensor types in the database.
    """
    result = sensors.list_sensor_types(session=session)
    return [SensorType(**sensor_type) for sensor_type in result]


@router.get("/list-measures", status_code=status.HTTP_200_OK)
def list_sensor_measures(session: Session = Depends(db_session)) -> list[SensorMeasure]:
    """
    List sensor measures in the database.
    """
    result = sensors.list_sensor_measures(session=session)
    return [SensorMeasure(**measure) for measure in result]


class SensorReadingsRequest(BaseModel):
    measure_name: str
    unique_identifier: str
    dt_from: datetime
    dt_to: datetime


class SensorReadingsResponse(BaseModel):
    value: ValueType
    timestamp: datetime


@router.post("/sensor-readings", status_code=status.HTTP_200_OK)
def get_sensor_readings(
    payload: SensorReadingsRequest, session: Session = Depends(db_session)
) -> list[SensorReadingsResponse]:
    """
    Get sensor readings for a specific measure and sensor between two dates.
    """
    readings = sensors.get_sensor_readings(**payload.model_dump(), session=session)
    return [
        SensorReadingsResponse(value=reading[0], timestamp=reading[1])
        for reading in readings
    ]


class DeleteSensorRequest(BaseModel):
    unique_identifier: str


@router.post("/delete-sensor", status_code=status.HTTP_200_OK)
def delete_sensor(
    payload: DeleteSensorRequest, session: Session = Depends(db_session)
) -> MessageResponse:
    """
    Delete a sensor from the database.
    """
    sensors.delete_sensor(unique_identifier=payload.unique_identifier, session=session)
    session.commit()
    return MessageResponse(detail="Sensor deleted")


class DeleteSensorTypeRequest(BaseModel):
    type_name: str


@router.post("/delete-sensor-type", status_code=status.HTTP_200_OK)
def delete_sensor_type(
    payload: DeleteSensorTypeRequest, session: Session = Depends(db_session)
) -> MessageResponse:
    """
    Delete a sensor type from the database.
    """
    sensors.delete_sensor_type(type_name=payload.type_name, session=session)
    session.commit()
    return MessageResponse(detail="Sensor type deleted")


class EditSensorRequest(BaseModel):
    unique_identifier: str
    name: str
    notes: str


@router.post(
    "/edit-sensor",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_400_BAD_REQUEST: {"model": MessageResponse}},
)
def edit_sensor(
    payload: EditSensorRequest, session: Session = Depends(db_session)
) -> MessageResponse:
    """
    Edit a sensor in the database.

    The `unique_identifier` field identifies the sensor, the `name` and `notes` fields
    are the new values.
    """
    try:
        sensors.edit_sensor(
            unique_identifier=payload.unique_identifier,
            new_name=payload.name,
            new_notes=payload.notes,
            session=session,
        )
        session.commit()
    except RowMissingError:
        raise HTTPException(status_code=400, detail="Sensor does not exist")
    return MessageResponse(detail="Sensor edited")
