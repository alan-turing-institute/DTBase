"""
A module for the routes under /services.
"""
import http.client
import json
from typing import Any, Optional

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from pydantic import BaseModel

from dtbase.webapp.app.base.forms import NewServiceForm
from dtbase.webapp.app.services import blueprint


@blueprint.route("/index", methods=["GET", "POST"])
@login_required
def index() -> str:
    """Index page."""
    new_service_form = NewServiceForm(request.form)
    if request.method == "POST":
        if "submitDelete" in request.form:
            payload = {"name": request.form["name"]}
            response = current_user.backend_call(
                "post", "/service/delete-service", payload=payload
            )
            if response.status_code == 200:
                flash("Service deleted successfully", "success")
            else:
                flash("Failed to delete service", "error")
        else:
            new_service_form.validate_on_submit()
            payload = {
                "name": request.form["name"],
                "url": request.form["url"],
                "http_method": request.form["http_method"],
            }
            response = current_user.backend_call(
                "post", "/service/insert-service", payload=payload
            )
            if response.status_code == 201:
                flash("Service created successfully", "success")
            else:
                flash("Failed to create service", "error")

    response = current_user.backend_call("get", "/service/list-services")
    services = response.json()
    return render_template(
        "services.html", services=services, new_service_form=new_service_form
    )


# TODO This should probably rather be imported from core.
class Service(BaseModel):
    """Service model."""

    name: str
    url: str
    http_method: str


class ParameterSet(BaseModel):
    """Parameter set model."""

    service_name: str
    name: str
    parameters: dict[str, Any]


def _get_service_details(request_args: Any) -> Service:
    """Get details of the current selected service."""
    service_name = request_args.get("service_name")
    response = current_user.backend_call("get", "/service/list-services")
    if response.status_code != 200:
        flash("Failed to retrieve list of services", "error")
    services = [Service(**s) for s in response.json()]
    service = next((x for x in services if x.name == service_name), None)
    if service is None:
        flash(f"Service {service_name} not found", "error")
        raise ValueError(f"Service {service_name} not found")
    return service


def _get_current_parameter_set(
    parameter_sets: list[ParameterSet], set_name: Optional[str]
) -> Optional[ParameterSet]:
    if set_name is None:
        return None
    parameter_set = next((x for x in parameter_sets if x.name == set_name), None)
    if parameter_set is None:
        flash(f"Parameter set {set_name} not found", "error")
    return parameter_set


def _get_parameter_sets(service: Service) -> list[ParameterSet]:
    response = current_user.backend_call(
        "post", "/service/list-parameter-sets", payload={"service_name": service.name}
    )
    if response.status_code != 200:
        flash("Failed to retrieve parameter sets", "error")
    parameter_sets = [ParameterSet(**s) for s in response.json()]
    return parameter_sets


def _handle_save(
    service: Service, current_parameter_set: ParameterSet, parameters: dict[str, Any]
) -> None:
    """Handle saving the service details."""
    payload = current_parameter_set.model_dump() | {"parameters": parameters}
    response = current_user.backend_call(
        "post", "/service/edit-parameter-set", payload=payload
    )
    if response.status_code == 200:
        flash("Parameter set edited successfully", "success")
    else:
        flash("Failed to edit parameter set", "error")


def _handle_run_current(
    service: Service,
    current_parameter_set: Optional[ParameterSet],
    parameters: dict[str, Any],
) -> None:
    payload = {
        "service_name": service.name,
        "parameter_set_name": current_parameter_set.name
        if current_parameter_set is not None
        else None,
        "parameters": parameters,
    }
    response = current_user.backend_call(
        "post", "/service/run-service", payload=payload
    )
    if response.status_code == 200:
        flash("Service called", "success")
    else:
        flash("Failed to call service", "error")


def _handle_add_new_set(service: Service, new_parameter_set_name: str) -> ParameterSet:
    new_parameter_set = ParameterSet.construct(
        service_name=service.name,
        name=new_parameter_set_name,
        parameters={},
    )
    response = current_user.backend_call(
        "post", "/service/insert-parameter-set", payload=new_parameter_set.model_dump()
    )
    if response.status_code == 201:
        flash("Parameter set created successfully", "success")
    else:
        flash("Failed to create parameter set", "error")
    return new_parameter_set


def _handle_delete(service: Service, parameter_set_name_to_delete: str) -> None:
    payload = {
        "service_name": service.name,
        "name": parameter_set_name_to_delete,
    }
    response = current_user.backend_call(
        "post", "/service/delete-parameter-set", payload=payload
    )
    if response.status_code == 200:
        flash("Parameter set deleted successfully", "success")
    else:
        flash("Failed to delete parameter set", "error")


def _handle_run_named(service: Service, parameter_set_name_to_run: str) -> None:
    payload = {
        "service_name": service.name,
        "parameter_set_name": parameter_set_name_to_run,
    }
    response = current_user.backend_call(
        "post", "/service/run-service", payload=payload
    )
    if response.status_code == 200:
        flash("Service called", "success")
    else:
        flash("Failed to call service", "error")


def _get_run_history(service: Service) -> list[dict[str, Any]]:
    """Get the call history of the service."""
    response = current_user.backend_call(
        "post", "/service/list-runs", payload={"service_name": service.name}
    )
    runs = response.json()
    if response.status_code != 200 or runs is None:
        flash("Failed to retrieve run history", "error")
    runs = list(sorted(runs, key=lambda x: x["timestamp"], reverse=True))
    return runs


@blueprint.route("/details", methods=["GET", "POST"])
@login_required
def details() -> str:
    """Index page."""
    try:
        service = _get_service_details(request.args)
    except ValueError:
        return redirect(url_for("services_blueprint.index"))

    # Get parameter sets and the currently selected parameter set in particular, if any
    parameter_sets = _get_parameter_sets(service)
    current_parameter_set = _get_current_parameter_set(
        parameter_sets, request.form.get("current_parameter_set_name")
    )

    # Get the current contents of the parameters textarea.
    if "parameters" in request.form:
        parameters = json.loads(request.form["parameters"])
    else:
        parameters = {}

    if request.method == "POST":
        if "submitSaveCurrent" in request.form:
            assert current_parameter_set is not None
            _handle_save(service, current_parameter_set, parameters)

        elif "submitRunCurrent" in request.form:
            _handle_run_current(service, current_parameter_set, parameters)

        elif "submitAddNewSet" in request.form:
            new_parameter_set_name = request.form["new_parameter_set_name"]
            current_parameter_set = _handle_add_new_set(service, new_parameter_set_name)
            parameters = current_parameter_set.parameters
            parameter_sets = _get_parameter_sets(service)

        elif "submitEditNamed" in request.form:
            current_parameter_set = _get_current_parameter_set(
                parameter_sets, request.form["submitEditNamed"]
            )
            assert current_parameter_set is not None
            parameters = current_parameter_set.parameters

        elif "submitDeleteNamed" in request.form:
            _handle_delete(service, request.form["submitDeleteNamed"])
            parameter_sets = _get_parameter_sets(service)

        elif "submitRunNamed" in request.form:
            _handle_run_named(service, request.form["submitRunNamed"])

    run_history = _get_run_history(service)
    # Get the verbal descriptions of return status codes, and associate them with
    # colours.
    for run in run_history:
        status_code = run["response_status_code"]
        run["status_description"] = http.client.responses.get(
            status_code, "Unknown status"
        )
        if status_code < 200:
            run["status_colour"] = "#040078"
        elif 200 <= status_code < 300:
            run["status_colour"] = "#147800"
        elif 300 <= status_code < 400:
            run["status_colour"] = "#54652A"
        elif 400 <= status_code < 500:
            run["status_colour"] = "#780000"
        else:
            run["status_colour"] = "#784E00"

    return render_template(
        "service_details.html",
        service=service,
        parameters=parameters,
        parameter_set=current_parameter_set,
        parameter_sets=parameter_sets,
        run_history=run_history,
    )
