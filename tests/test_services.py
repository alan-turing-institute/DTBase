"""
Test the functions for accessing the services tables.
"""
import datetime as dt
from unittest import mock

import pytest
import requests_mock
from sqlalchemy.orm import Session

from dtbase.backend.database import service
from dtbase.backend.exc import RowExistsError, RowMissingError

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


def test_edit_parameter_set(session: Session) -> None:
    """
    Test the edit_parameter_set function.
    """
    insert_parameter_sets(session)
    service.edit_parameter_set(
        service_name=SERVICE1_NAME,
        name=SERVICE_PARAMETERS1_NAME,
        parameters={"new_param": "new_value"},
        session=session,
    )
    session.commit()
    assert service.list_parameter_sets(service_name=SERVICE1_NAME, session=session) == [
        {
            "service_name": SERVICE1_NAME,
            "name": SERVICE_PARAMETERS1_NAME,
            "parameters": {"new_param": "new_value"},
        },
        {
            "service_name": SERVICE1_NAME,
            "name": SERVICE_PARAMETERS2_NAME,
            "parameters": SERVICE_PARAMETERS2,
        },
    ]


def test_edit_parameter_set_nonexistent(session: Session) -> None:
    """
    Test the edit_parameter_set function.
    """
    with pytest.raises(RowMissingError):
        service.edit_parameter_set(
            service_name=SERVICE1_NAME,
            name=SERVICE_PARAMETERS1_NAME,
            parameters={"new_param": "new_value"},
            session=session,
        )


def test_delete_service(session: Session) -> None:
    """
    Test the delete_service function.
    """
    insert_services(session)
    service.delete_service(service_name=SERVICE1_NAME, session=session)
    assert service.list_services(session) == [
        {
            "name": SERVICE2_NAME,
            "url": SERVICE2_URL,
            "http_method": SERVICE2_METHOD,
        },
    ]


def test_delete_service_non_existent(session: Session) -> None:
    """
    Test the delete_service function with a service that doesn't exist.
    """
    insert_services(session)
    with pytest.raises(RowMissingError):
        service.delete_service(service_name="No such service", session=session)


def test_delete_parameter_set(session: Session) -> None:
    """
    Test the delete_parameter_set function.
    """
    insert_parameter_sets(session)
    service.delete_parameter_set(
        service_name=SERVICE1_NAME, name=SERVICE_PARAMETERS1_NAME, session=session
    )
    expected_values = [
        {
            "name": SERVICE_PARAMETERS2_NAME,
            "parameters": SERVICE_PARAMETERS2,
            "service_name": SERVICE1_NAME,
        },
    ]
    assert service.list_parameter_sets(session=session) == expected_values


def test_delete_parameter_set_non_existent(session: Session) -> None:
    """
    Test the delete_parameter_set function with a set that doesn't exist.
    """
    insert_parameter_sets(session)
    with pytest.raises(RowMissingError):
        service.delete_parameter_set(
            service_name=SERVICE1_NAME, name="No such set", session=session
        )


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
    insert_parameter_sets(session)
    with requests_mock.Mocker() as m:
        TEST_RETURN = {"message": "Well hello there"}
        m.post(SERVICE1_URL, json=TEST_RETURN)
        service.run_service(
            service_name=SERVICE1_NAME,
            parameter_set_name=SERVICE_PARAMETERS1_NAME,
            parameters={"param1": "value1"},
            session=session,
        )


def test_list_runs(session: Session) -> None:
    """
    Test the run_service function.

    The steps in this test are:

     1. Insert parameter sets
     2. Mock Service 1 and Service 2
     3. Run Service 1 four times, and Service 2 once with different parameters
     4. Assert lenth of returned run list for each Service
     5. Assert length of run list for Service 1 with a certain parameter combination
     6. Assert length of run list for all runs
     7. Assert the contents of each run in run list
    """
    insert_parameter_sets(session)
    now = dt.datetime(2021, 1, 1, tzinfo=dt.timezone.utc)
    with requests_mock.Mocker() as m, mock.patch(
        "dtbase.backend.database.service.dt"
    ) as mock_dt:
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
        test_params = {"param1": "value1"}
        service.run_service(
            service_name=SERVICE1_NAME,
            parameter_set_name=SERVICE_PARAMETERS2_NAME,
            parameters=test_params,
            session=session,
        )
        session.commit()

        runs = service.list_runs(service_name=SERVICE1_NAME, session=session)
        assert len(runs) == 4
        runs = service.list_runs(service_name=SERVICE2_NAME, session=session)
        assert len(runs) == 1
        runs = service.list_runs(
            service_name=SERVICE1_NAME,
            parameter_set_name=SERVICE_PARAMETERS2_NAME,
            session=session,
        )
        assert len(runs) == 2
        runs = service.list_runs(session=session)
        assert len(runs) == 5

        expected_run1 = {
            "service_name": SERVICE1_NAME,
            "parameter_set_name": SERVICE_PARAMETERS1_NAME,
            "parameters": SERVICE_PARAMETERS1,
            "timestamp": now,
            "response_json": test_return,
            "response_status_code": 200,
        }
        expected_run2 = {
            "service_name": SERVICE2_NAME,
            "parameter_set_name": None,
            "parameters": test_params,
            "timestamp": now,
            "response_json": None,
            "response_status_code": 404,
        }
        expected_run3 = {
            "service_name": SERVICE1_NAME,
            "parameter_set_name": SERVICE_PARAMETERS2_NAME,
            "parameters": SERVICE_PARAMETERS2,
            "timestamp": now,
            "response_json": test_return,
            "response_status_code": 200,
        }
        expected_run4 = {
            "service_name": SERVICE1_NAME,
            "parameter_set_name": SERVICE_PARAMETERS2_NAME,
            "parameters": test_params,
            "timestamp": now,
            "response_json": test_return,
            "response_status_code": 200,
        }
        assert expected_run1 in runs
        assert expected_run2 in runs
        assert expected_run3 in runs
        assert expected_run4 in runs
