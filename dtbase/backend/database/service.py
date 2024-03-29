"""Functions for accessing the service tables. """
import datetime as dt
from typing import Any, List, Literal, Optional

import requests
import sqlalchemy as sqla
from sqlalchemy.exc import IntegrityError

from dtbase.backend.database import utils
from dtbase.backend.database.structure import (
    Service,
    ServiceParameterSet,
    ServiceRunLog,
)
from dtbase.backend.database.utils import Session
from dtbase.backend.exc import RowExistsError, RowMissingError

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


def insert_parameter_set(
    service_name: str, name: str, parameters: dict, session: Session
) -> None:
    """
    Inserts new parameter set into the database.
    """
    service_id = get_service_id(service_name, session)
    new_parameters = ServiceParameterSet(
        service_id=service_id, parameters=parameters, name=name
    )
    session.add(new_parameters)
    session.flush()


def list_services(session: Session) -> List[dict[str, Any]]:
    """
    Return all services from the database.
    """
    result = (
        session.execute(sqla.select(Service.name, Service.url, Service.http_method))
        .mappings()
        .all()
    )
    result = utils.row_mappings_to_dicts(result)
    return result


def list_parameter_sets(
    session: Session, service_name: Optional[str] = None
) -> List[dict[str, Any]]:
    """
    Return all parameter sets from the database.

    Args:
        session: SQLAlchemy session.
        service_name: Optional service name. If None (default), return parameter sets
        for all services.

    Return:
        List of rows from the ServiceParameterSet table, as dictionaries.
    """
    query = sqla.select(
        ServiceParameterSet.name,
        Service.name.label("service_name"),
        ServiceParameterSet.parameters,
    ).join(Service, Service.id == ServiceParameterSet.service_id)
    if service_name is not None:
        query = query.where(Service.name == service_name)
    result = session.execute(query).mappings().all()
    result = utils.row_mappings_to_dicts(result)
    return result


def delete_service(service_name: str, session: Session) -> None:
    """
    Deletes a service from the database.
    """
    result = session.execute(sqla.delete(Service).where(Service.name == service_name))
    if result.rowcount == 0:
        raise RowMissingError(f"No service with name {service_name} exists.")
    session.flush()


def delete_parameter_set(service_name: str, name: str, session: Session) -> None:
    """
    Deletes service parameter set from the database.
    """
    service_id = get_service_id(service_name, session)
    result = session.execute(
        sqla.delete(ServiceParameterSet).where(
            (ServiceParameterSet.service_id == service_id)
            & (ServiceParameterSet.name == name)
        )
    )
    if result.rowcount == 0:
        raise RowMissingError(
            f"No parameter set for service {service_name} with name "
            f"{service_name} exists."
        )
    session.flush()


def edit_parameter_set(
    service_name: str,
    name: str,
    parameters: dict,
    session: Session,
) -> None:
    """
    Edits a parameter set in the database.
    """
    service_id = get_service_id(service_name, session)
    query_result = (
        session.query(ServiceParameterSet)
        .filter(ServiceParameterSet.service_id == service_id)
        .filter(ServiceParameterSet.name == name)
        .scalar()
    )
    if query_result is None:
        raise RowMissingError(
            f"No parameter set with name {name} for service {service_name} exists."
        )
    query_result.parameters = parameters
    session.flush()


def run_service(
    service_name: str,
    session: Session,
    parameters: Optional[dict] = None,
    parameter_set_name: Optional[str] = None,
) -> None:
    """
    Runs a service with the given parameters.

    If parameter_set_name is provided but parameters is not, the stored parameters for
    the parameter set will be used.
    """
    service_query_result = (
        session.query(Service).filter(Service.name == service_name).scalar()
    )
    if service_query_result is None:
        raise RowMissingError(f"No service with name {service_name} exists.")
    url = service_query_result.url
    service_id = service_query_result.id
    method = service_query_result.http_method

    if parameter_set_name is not None:
        parameter_query_result = (
            session.query(ServiceParameterSet)
            .join(Service, Service.id == ServiceParameterSet.service_id)
            .filter(Service.name == service_name)
            .filter(ServiceParameterSet.name == parameter_set_name)
            .scalar()
        )
        if parameter_query_result is None:
            raise RowMissingError(
                f"No parameter set called {parameter_set_name} "
                f"for service {service_name}."
            )
        if parameters is None:
            parameters = parameter_query_result.parameters
        parameter_set_id = parameter_query_result.id
    else:
        parameter_set_id = None

    timestamp = dt.datetime.now()
    request_method = getattr(requests, method.lower())
    response = request_method(url, json=parameters)
    try:
        body = response.json()
    except requests.exceptions.JSONDecodeError:
        body = None
    new_log = ServiceRunLog(
        service_id=service_id,
        parameter_set_id=parameter_set_id,
        parameters=parameters,
        response_status_code=response.status_code,
        response_json=body,
        timestamp=timestamp,
    )
    session.add(new_log)
    session.flush()


def list_runs(
    session: Session,
    service_name: Optional[str] = None,
    parameter_set_name: Optional[str] = None,
) -> list[dict]:
    """
    Get the run history for a given service.

    Args:
        session: SQLAlchemy session.
        service_name: Optional service name. If None (default), return run history for
            all services.
        parameter_set_name: Optional service parameter set name. If None
            (default), return run history for all sets. Can only be provided if
            service_name is also provided.

    Returns:
        List of run history rows, as dictionaries.
    """
    if service_name is None and parameter_set_name is not None:
        raise ValueError("parameter_set_name cannot be provided without service_name.")

    query = (
        sqla.select(
            Service.name.label("service_name"),
            ServiceParameterSet.name.label("parameter_set_name"),
            ServiceRunLog.parameters,
            ServiceRunLog.response_status_code,
            ServiceRunLog.response_json,
            ServiceRunLog.timestamp,
        )
        .join(Service, Service.id == ServiceRunLog.service_id)
        .outerjoin(
            ServiceParameterSet,
            ServiceParameterSet.id == ServiceRunLog.parameter_set_id,
        )
    )
    if service_name is not None:
        query = query.where(Service.name == service_name)
    if parameter_set_name is not None:
        query = query.where(ServiceParameterSet.name == parameter_set_name)
    result = session.execute(query).mappings().all()
    result = utils.row_mappings_to_dicts(result)
    return result
