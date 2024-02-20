"""Functions for accessing the service tables. """
import datetime as dt
from typing import Any, List, Literal, Optional

import requests
import sqlalchemy as sqla
from sqlalchemy.exc import IntegrityError

from dtbase.core import utils
from dtbase.core.db import Session
from dtbase.core.exc import RowExistsError, RowMissingError
from dtbase.core.structure import Service, ServiceParameters, ServiceRunLog

HTTPMethods = Literal["GET", "POST", "PUT", "DELETE"]


def get_service_id(name: str, session: Session) -> int:
    """
    Get the service id for a given service name.
    """
    service_id = session.query(Service.id).filter(Service.name == name).scalar()
    if service_id is None:
        raise RowMissingError(f"No service with name {name} exists.")
    return service_id


def insert_service(
    name: str, url: str, http_method: HTTPMethods, session: Session
) -> None:
    """
    Inserts a new service into the database.
    """
    new_service = Service(name=name, url=url, http_method=http_method)
    session.add(new_service)
    try:
        session.flush()
    except IntegrityError:
        session.rollback()
        raise RowExistsError(f"A service with name {name} already exists.")


def insert_service_parameters(
    service_name: str, name: str, parameters: dict, session: Session
) -> None:
    """
    Inserts new service parameters into the database.
    """
    service_id = get_service_id(service_name, session)
    new_parameters = ServiceParameters(
        service_id=service_id, parameters=parameters, name=name
    )
    session.add(new_parameters)
    session.flush()


def list_services(session: Session) -> List[dict[str, Any]]:
    """
    Return all services from the database.
    """
    result = (
        session.execute(
            sqla.select(
                Service.name,
                Service.url,
                Service.http_method,
            )
        )
        .mappings()
        .all()
    )
    result = utils.row_mappings_to_dicts(result)
    return result


def list_service_parameters(
    session: Session, service_name: Optional[str] = None
) -> List[dict[str, Any]]:
    """
    Return all service parameters from the database.

    Args:
        session: SQLAlchemy session.
        service_name: Optional service name. If None (default), return parameters for
            all services.

    Return:
        List of rows from the ServiceParameters table, as dictionaries.
    """
    query = sqla.select(
        ServiceParameters.name,
        Service.name.label("service_name"),
        ServiceParameters.parameters,
    ).join(Service, Service.id == ServiceParameters.service_id)
    if service_name is not None:
        query = query.where(Service.name == service_name)
    result = session.execute(query).mappings().all()
    result = utils.row_mappings_to_dicts(result)
    return result


def delete_service(service_name: str, session: Session) -> None:
    """
    Deletes a service from the database.
    """
    session.query(Service).filter(Service.name == service_name).delete()
    session.flush()


def delete_service_parameters(service_name: str, name: str, session: Session) -> None:
    """
    Deletes service parameters from the database.
    """
    service_id = get_service_id(service_name, session)
    session.query(ServiceParameters).filter(
        ServiceParameters.service_id == service_id
    ).delete()
    session.flush()


def run_service(service_name: str, parameters_name: str, session: Session) -> None:
    """
    Runs a service with the given parameters.
    """
    service_parameters = (
        session.query(ServiceParameters)
        .join(Service, Service.id == ServiceParameters.service_id)
        .filter(Service.name == service_name)
        .filter(ServiceParameters.name == parameters_name)
        .one_or_none()
    )
    if service_parameters is None:
        raise RowMissingError(
            f"No parameters with name {parameters_name} for service {service_name}."
        )
    url = session.query(Service.url).filter(Service.name == service_name).scalar()
    if url is None:
        raise RowMissingError(f"No service with name {service_name} exists.")

    timestamp = dt.datetime.now()
    response = requests.post(url, json=service_parameters.parameters)
    service_id = get_service_id(service_name, session)
    new_log = ServiceRunLog(
        service_id=service_id,
        parameters_id=service_parameters.id,
        response_status_code=response.status_code,
        response=response.json(),
        timestamp=timestamp,
    )
    session.add(new_log)
    session.flush()


def list_service_runs(
    session: Session,
    service_name: Optional[str] = None,
    service_parameters_name: Optional[str] = None,
) -> list[dict]:
    """
    Get the run history for a given service.

    Args:
        session: SQLAlchemy session.
        service_name: Optional service name. If None (default), return run history for
            all services.
        service_parameters_name: Optional service parameters name. If None (default),
            return run history for all parameters. Can only be provided if service_name
            is also provided.

    Returns:
        List of run history rows, as dictionaries.
    """
    if service_name is None and service_parameters_name is not None:
        raise ValueError(
            "service_parameters_name cannot be provided without service_name."
        )

    query = (
        sqla.select(
            ServiceRunLog.id,
            Service.name.label("service_name"),
            ServiceParameters.name.label("parameters_name"),
            ServiceRunLog.response_status_code,
            ServiceRunLog.response,
            ServiceRunLog.timestamp,
        )
        .join(Service, Service.id == ServiceRunLog.service_id)
        .join(ServiceParameters, ServiceParameters.id == ServiceRunLog.parameters_id)
    )
    if service_name is not None:
        query = query.where(Service.name == service_name)
    if service_parameters_name is not None:
        query = query.where(ServiceParameters.name == service_parameters_name)
    result = session.execute(query).mappings().all()
    result = utils.row_mappings_to_dicts(result)
    return result
