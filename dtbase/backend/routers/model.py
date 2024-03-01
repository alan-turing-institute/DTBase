"""
Module (routes.py) to handle endpoints related to models
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, RootModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from dtbase.backend.auth import authenticate_access
from dtbase.backend.database import models
from dtbase.backend.database.utils import db_session
from dtbase.backend.models import (
    MessageResponse,
    Model,
    ModelMeasure,
    ModelScenario,
    SensorMeasureIdentifier,
    ValueType,
)
from dtbase.core.exc import RowMissingError

router = APIRouter(
    prefix="/model",
    tags=["model"],
    dependencies=[Depends(authenticate_access)],
    responses={status.HTTP_401_UNAUTHORIZED: {"model": MessageResponse}},
)


@router.post(
    "/insert-model",
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: {"model": MessageResponse}},
)
def insert_model(
    model: Model, session: Session = Depends(db_session)
) -> MessageResponse:
    """
    Add a model to the database.
    """
    try:
        models.insert_model(name=model.name, session=session)
        session.commit()
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Model exists already")
    return MessageResponse(detail="Model inserted")


@router.get("/list-models", status_code=status.HTTP_200_OK)
def list_models(session: Session = Depends(db_session)) -> list[Model]:
    """
    List all models in the database.
    """
    result = models.list_models(session=session)
    return [Model(**m) for m in result]


@router.post("/delete-model", status_code=status.HTTP_200_OK)
def delete_model(
    model: Model, session: Session = Depends(db_session)
) -> MessageResponse:
    """
    Delete a model from the database.
    """
    models.delete_model(model_name=model.name, session=session)
    session.commit()
    return MessageResponse(detail="Model deleted")


@router.post(
    "/insert-model-scenario",
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: {"model": MessageResponse}},
)
def insert_model_scenario(
    scenario: ModelScenario,
    session: Session = Depends(db_session),
) -> MessageResponse:
    """
    Insert a model scenario into the database.

    A model scenario specifies parameters for running a model. It is always tied to a
    particular model. It comes with a free form text description only (can also be
    null).
    """

    try:
        models.insert_model_scenario(**scenario.model_dump(), session=session)
        session.commit()
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Scenario exists already")
    return MessageResponse(detail="Model scenario inserted")


@router.get("/list-model-scenarios", status_code=status.HTTP_200_OK)
def list_model_scenarios(session: Session = Depends(db_session)) -> list[ModelScenario]:
    """
    List all model scenarios in the database.
    """
    result = models.list_model_scenarios(session=session)
    return [ModelScenario(**m) for m in result]


@router.post("/delete-model-scenario", status_code=status.HTTP_200_OK)
def delete_model_scenario(
    scenario: ModelScenario, session: Session = Depends(db_session)
) -> MessageResponse:
    """
    Delete a model scenario from the database.
    """
    models.delete_model_scenario(**scenario.model_dump(), session=session)
    session.commit()
    return MessageResponse(detail="Model scenario deleted")


@router.post("/insert-model-measure", status_code=status.HTTP_201_CREATED)
def insert_model_measure(
    model_measure: ModelMeasure, session: Session = Depends(db_session)
) -> MessageResponse:
    """
    Add a model measure to the database.

    Model measures specify quantities that models can output, such as "mean temperature"
    or "upper 90% confidence limit for relative humidity".

    The datatype has to be one of "string", "integer", "float", or "boolean"
    """
    models.insert_model_measure(**model_measure.model_dump(), session=session)
    session.commit()
    return MessageResponse(detail="Model measure inserted")


@router.get("/list-model-measures", status_code=status.HTTP_200_OK)
def list_models_measures(session: Session = Depends(db_session)) -> list[ModelMeasure]:
    """
    List all model measures in the database.
    """
    model_measures = models.list_model_measures(session=session)
    return [ModelMeasure(**m) for m in model_measures]


class DeleteModelMeasureRequest(BaseModel):
    name: str


@router.post("/delete-model-measure", status_code=status.HTTP_200_OK)
def delete_model_measure(
    payload: DeleteModelMeasureRequest, session: Session = Depends(db_session)
) -> MessageResponse:
    """Delete a model measure from the database."""
    models.delete_model_measure(name=payload.name, session=session)
    session.commit()
    return MessageResponse(detail="Model measure deleted")


class MeasureResults(BaseModel):
    measure_name: str
    values: list[ValueType]
    timestamps: list[datetime]


class InsertModelRunRequest(BaseModel):
    model_name: str
    scenario_description: str
    measures_and_values: list[MeasureResults]
    time_created: datetime = Field(default_factory=datetime.now)
    create_scenario: bool = Field(default=False)
    sensor_unique_id: Optional[str] = Field(default=None)
    sensor_measure: Optional[SensorMeasureIdentifier] = Field(default=None)

    # Needed because the field `model_name` conflicts with some Pydantic internals.
    model_config = ConfigDict(protected_namespaces=())


@router.post("/insert-model-run", status_code=status.HTTP_201_CREATED)
def insert_model_run(
    payload: InsertModelRunRequest, session: Session = Depends(db_session)
) -> MessageResponse:
    """
    Add a model run to the database.

    The `measures_and_values`, which holds the results of the model, should have as many
    entries as this model records measures. The values can be strings, integers, floats,
    or booleans, depending on the measure. There should as many values as there are
    timestamps.
    """
    models.insert_model_run(**payload.model_dump(), session=session)
    session.commit()
    return MessageResponse(detail="Model run inserted")


class ListModelRunsRequest(BaseModel):
    model_name: str
    dt_from: datetime = Field(
        default_factory=(lambda: datetime.now() - timedelta(weeks=1))
    )
    dt_to: datetime = Field(default_factory=datetime.now)
    scenario: Optional[str] = Field(default=None)

    # Needed because the field `model_name` conflicts with some Pydantic internals.
    model_config = ConfigDict(protected_namespaces=())


class ModelRunResponse(BaseModel):
    id: int
    model_id: int
    model_name: str
    scenario_id: int
    scenario_description: str
    time_created: datetime
    sensor_unique_id: Optional[str] = Field(default=None)
    sensor_measure: Optional[SensorMeasureIdentifier] = Field(default=None)

    # Needed because the field `model_name` conflicts with some Pydantic internals.
    model_config = ConfigDict(protected_namespaces=())


@router.post("/list-model-runs", status_code=status.HTTP_200_OK)
def list_model_runs(
    payload: ListModelRunsRequest, session: Session = Depends(db_session)
) -> list[ModelRunResponse]:
    """
    List all model runs in the database.

    The model name is required, the time range and scenario are optional. By default the
    time range is the last week and all scenarios are accepted.
    """
    model_runs = models.list_model_runs(**payload.model_dump(), session=session)
    return [ModelRunResponse(**m) for m in model_runs]


class GetModelRunRequest(BaseModel):
    run_id: int


class ModelValueDatapoint(BaseModel):
    value: ValueType
    timestamp: datetime


GetModelRunResponse = RootModel[dict[str, list[ModelValueDatapoint]]]


@router.post("/get-model-run", status_code=status.HTTP_200_OK)
def get_model_run(
    payload: GetModelRunRequest, session: Session = Depends(db_session)
) -> GetModelRunResponse:
    """
    Get the output of a model run.

    The keys in the return value or the measures that this model returns.
    """
    model_run = models.get_model_run_results(payload.run_id, session=session)
    return GetModelRunResponse(
        {
            k: [ModelValueDatapoint(value=t[0], timestamp=t[1]) for t in v]
            for k, v in model_run.items()
        }
    )


class GetModelRunSensorMeasureRequest(BaseModel):
    run_id: int


class ModelRunSensorMeasureResponse(BaseModel):
    sensor_unique_id: Optional[str]
    sensor_measure: Optional[SensorMeasureIdentifier]


@router.post(
    "/get-model-run-sensor-measure",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_400_BAD_REQUEST: {"model": MessageResponse}},
)
def get_model_run_sensor_measure(
    payload: GetModelRunSensorMeasureRequest, session: Session = Depends(db_session)
) -> ModelRunSensorMeasureResponse:
    """
    Get the sensor and sensor measure that the output of a model run should be compared
    to.
    """
    try:
        result = models.get_model_run_sensor_measure(
            **payload.model_dump(), session=session
        )
    except RowMissingError:
        raise HTTPException(status_code=400, detail="No such model run")
    return ModelRunSensorMeasureResponse(**result)
