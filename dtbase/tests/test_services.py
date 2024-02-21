"""
Test the functions for accessing the services tables.
"""
import datetime as dt
from unittest import mock

import pytest
import requests_mock
from sqlalchemy.orm import Session

from dtbase.core import service
from dtbase.core.exc import RowExistsError, RowMissingError

SERVICE1_NAME = "Test Service"
SERVICE1_URL = "http://test.service/is-not-a-real-thing"
SERVICE1_METHOD = "POST"

SERVICE2_NAME = "Second test Service"
SERVICE2_URL = "http://test.service/this-isnt-really-real-either"
SERVICE2_METHOD = "GET"

SERVICE_PARAMETERS1_NAME = "Test parameter set"
SERVICE_PARAMETERS1 = {
    "param1": "value1",
    "param2": "value2",
    "param3": "value3",
}

SERVICE_PARAMETERS2_NAME = "A second test parameter set"
SERVICE_PARAMETERS2 = {
    "param1": "value1",
    "param2": "value2",
}


def insert_services(session: Session) -> None:
    """
    Insert a service into the database.
    """
    service.insert_service(
        name=SERVICE1_NAME,
        url=SERVICE1_URL,
        http_method=SERVICE1_METHOD,
        session=session,
    )
    service.insert_service(
        name=SERVICE2_NAME,
        url=SERVICE2_URL,
        http_method=SERVICE2_METHOD,
        session=session,
    )
    session.commit()


def insert_parameter_sets(session: Session) -> None:
    """
    Insert a service parameters set into the database.
    """
    insert_services(session)
    service.insert_parameter_set(
        SERVICE1_NAME, SERVICE_PARAMETERS1_NAME, SERVICE_PARAMETERS1, session=session
    )
    service.insert_parameter_set(
        SERVICE1_NAME, SERVICE_PARAMETERS2_NAME, SERVICE_PARAMETERS2, session=session
    )
    session.commit()


def test_insert_service(session: Session) -> None:
    """
    Test the insert_service function.
    """
    insert_services(session)


def test_list_service(session: Session) -> None:
    """
    Test the insert_service function.
    """
    insert_services(session)
    service_list = service.list_services(session)
    assert len(service_list) == 2
    assert service_list == [
        {
            "name": SERVICE1_NAME,
            "url": SERVICE1_URL,
            "http_method": SERVICE1_METHOD,
        },
        {
            "name": SERVICE2_NAME,
            "url": SERVICE2_URL,
            "http_method": SERVICE2_METHOD,
        },
    ]


def test_insert_service_duplicate(session: Session) -> None:
    """
    Test the insert_service function with a duplicate service name.
    """
    insert_services(session)
    with pytest.raises(RowExistsError):
        insert_services(session)


def test_insert_parameter_set(session: Session) -> None:
    """
    Test the insert_parameter_set function.
    """
    insert_parameter_sets(session)


def test_list_parameter_sets(session: Session) -> None:
    """
    Test the list_parameter_sets function.
    """
    insert_parameter_sets(session)
    expected_values = [
        {
            "name": SERVICE_PARAMETERS1_NAME,
            "parameters": SERVICE_PARAMETERS1,
            "service_name": SERVICE1_NAME,
        },
        {
            "name": SERVICE_PARAMETERS2_NAME,
            "parameters": SERVICE_PARAMETERS2,
            "service_name": SERVICE1_NAME,
        },
    ]
    assert (
        service.list_parameter_sets(service_name=SERVICE1_NAME, session=session)
        == expected_values
    )
    assert service.list_parameter_sets(session=session) == expected_values
    assert (
        service.list_parameter_sets(service_name=SERVICE2_NAME, session=session) == []
    )


def test_insert_parameter_set_duplicate(session: Session) -> None:
    """
    Test the insert_parameter_set function with a duplicate parameter set name.
    """
    insert_parameter_sets(session)
    with pytest.raises(RowExistsError):
        insert_parameter_sets(session)


def test_run_service_with_parameter_set(session: Session) -> None:
    """
    Test the run_service function.
    """
    insert_parameter_sets(session)
    with requests_mock.Mocker() as m:
        TEST_RETURN = {"message": "Well hello there"}
        m.post(SERVICE1_URL, json=TEST_RETURN)
        service.run_service(
            service_name=SERVICE1_NAME,
            parameter_set_name=SERVICE_PARAMETERS1_NAME,
            session=session,
        )


def test_run_service_with_nonexistent_parameter_set(session: Session) -> None:
    """
    Test the run_service function.
    """
    with pytest.raises(RowMissingError):
        service.run_service(
            service_name=SERVICE1_NAME,
            parameter_set_name=SERVICE_PARAMETERS1_NAME,
            session=session,
        )


def test_run_service_with_parameters(session: Session) -> None:
    """
    Test the run_service function.
    """
    insert_parameter_sets(session)
    with requests_mock.Mocker() as m:
        TEST_RETURN = {"message": "Well hello there"}
        m.post(SERVICE1_URL, json=TEST_RETURN)
        service.run_service(
            service_name=SERVICE1_NAME,
            parameters={"param1": "value1"},
            session=session,
        )


def test_run_service_with_conflicting_parameters(session: Session) -> None:
    """
    Test the run_service function.
    """
    insert_services(session)
    with pytest.raises(ValueError):
        service.run_service(
            service_name=SERVICE1_NAME,
            parameter_set_name=SERVICE_PARAMETERS1_NAME,
            parameters={"param1": "value1"},
            session=session,
        )


def test_list_service_runs(session: Session) -> None:
    """
    Test the run_service function.
    """
    insert_parameter_sets(session)
    now = dt.datetime(2021, 1, 1, tzinfo=dt.timezone.utc)
    with requests_mock.Mocker() as m, mock.patch("dtbase.core.service.dt") as mock_dt:
        mock_dt.datetime.now.return_value = now
        test_return = {"message": "Well hello there"}
        m.post(SERVICE1_URL, json=test_return)
        m.get(SERVICE2_URL, json=None, status_code=404)

        service.run_service(
            service_name=SERVICE1_NAME,
            parameter_set_name=SERVICE_PARAMETERS1_NAME,
            session=session,
        )
        service.run_service(
            service_name=SERVICE1_NAME,
            parameter_set_name=SERVICE_PARAMETERS1_NAME,
            session=session,
        )
        service.run_service(
            service_name=SERVICE1_NAME,
            parameter_set_name=SERVICE_PARAMETERS2_NAME,
            session=session,
        )
        test_params = {"param1": "value1"}
        service.run_service(
            service_name=SERVICE2_NAME,
            parameters=test_params,
            session=session,
        )
        session.commit()

        runs = service.list_service_runs(service_name=SERVICE1_NAME, session=session)
        assert len(runs) == 3
        runs = service.list_service_runs(service_name=SERVICE2_NAME, session=session)
        assert len(runs) == 1
        runs = service.list_service_runs(
            service_name=SERVICE1_NAME,
            parameter_set_name=SERVICE_PARAMETERS2_NAME,
            session=session,
        )
        assert len(runs) == 1
        runs = service.list_service_runs(session=session)
        assert len(runs) == 4

        expected_run1 = {
            "id": 1,
            "service_name": SERVICE1_NAME,
            "parameter_set_name": SERVICE_PARAMETERS1_NAME,
            "parameters": SERVICE_PARAMETERS1,
            "timestamp": now,
            "response_json": test_return,
            "response_status_code": 200,
        }
        expected_run2 = {
            "id": 4,
            "service_name": SERVICE2_NAME,
            "parameter_set_name": None,
            "parameters": test_params,
            "timestamp": now,
            "response_json": None,
            "response_status_code": 404,
        }
        assert expected_run1 in runs
        assert expected_run2 in runs
