"""
A module for the main dashboard actions
"""
import datetime as dt
from typing import Any, Dict, List, Optional

from flask import render_template, request
from flask_login import current_user, login_required

from dtbase.webapp.app.models import blueprint


def fetch_all_models() -> List[dict[str, Any]]:
    """Get all models from the database.

    Args:
        None
    Returns:
        List of dicts, one for each model
    """
    response = current_user.backend_call("get", "/model/list-models")
    if response.status_code != 200:
        raise RuntimeError(f"A backend call failed: {response}")
    models = response.json()
    return models


def fetch_all_scenarios() -> List[dict[str, Any]]:
    """Get all model scenarios from the database.

    Args:
        None
    Returns:
        List of dicts, one for each model
    """
    response = current_user.backend_call("get", "/model/list-model-scenarios")
    if response.status_code != 200:
        raise RuntimeError(f"A backend call failed: {response}")
    scenarios = response.json()
    return scenarios


def get_runs(
    model_name: str,
    dt_from: dt.datetime,
    dt_to: dt.datetime,
    scenario_description: Optional[str],
) -> List[dict[str, Any]]:
    """
    Get all the model runs fitting the arguments.

    Args:
        model:str, the name of the model to search for
        dt_from:datetime, earliest time for the model run
        dt_to:datetime, latest time for the model run
        scenario:str, model scenario, optional
    Returns:
        run_id:int
    """
    payload = {
        "model_name": model_name,
        "dt_from": dt_from.isoformat(),
        "dt_to": dt_to.isoformat(),
        "scenario": scenario_description,
    }
    response = current_user.backend_call("get", "/model/list-model-runs", payload)
    if response.status_code != 200:
        raise RuntimeError(f"A backend call failed: {response}")
    runs = response.json()
    return runs


def get_run_pred_data(run_id: int | str) -> Dict[str, Any]:
    """
    Get the predicted outputs of the specified run.

    Args:
        run_id:int | str, database ID of the ModelRun
    Returns:
        dict, keyed by ModelMeasure, containing list of dicts
        {"timestamp":<ts:str>, "value": <val:int|float|str|bool>}
    """
    response = current_user.backend_call(
        "get", "/model/get-model-run", {"run_id": run_id}
    )
    if response.status_code != 200:
        raise RuntimeError(f"A backend call failed: {response}")
    pred_data = response.json()
    return pred_data


def get_run_sensor_data(run_id: int | str, earliest_timestamp: str) -> Dict[str, Any]:
    """
    Get the real data to which the prediction of a ModelRun should be compared

    Args:
       run_id: int | str, database ID of the ModelRun
       earliest_timestamp: str, ISO format timestamp of the earliest prediction point

    Returns:
       dict, with keys "sensor_uniq_id", "measure_name", "readings", where "readings" is
       a list of (value, timestamp) tuples.
    """
    response = current_user.backend_call(
        "get", "/model/get-model-run-sensor-measure", {"run_id": run_id}
    )
    if response.status_code != 200:
        raise RuntimeError(f"A backend call failed: {response}")
    measure_name = response.json()["sensor_measure"]["name"]
    sensor_uniq_id = response.json()["sensor_unique_id"]
    dt_from = earliest_timestamp
    dt_to = dt.datetime.now().isoformat()
    response = current_user.backend_call(
        "get",
        "/sensor/sensor-readings",
        payload={
            "measure_name": measure_name,
            "unique_identifier": sensor_uniq_id,
            "dt_from": dt_from,
            "dt_to": dt_to,
        },
    )
    if response.status_code != 200:
        raise RuntimeError(f"A backend call failed: {response}")
    readings = response.json()
    return {
        "sensor_uniq_id": sensor_uniq_id,
        "measure_name": measure_name,
        "readings": readings,
    }


def fetch_run_data(run_id: int | str) -> Dict[str, Any]:
    """
    Fetch all the info for the latest prediction run for a given model.

    Args:
       run_id:int | str, identifier of the model run.
    Returns:
       dict, with keys "pred_data", "sensor_data".
    """
    pred_data = get_run_pred_data(run_id)
    # find the earliest time in the predicted data
    earliest_timestamp = pred_data[list(pred_data.keys())[0]][0]["timestamp"]
    sensor_data = get_run_sensor_data(run_id, earliest_timestamp)
    return {"pred_data": pred_data, "sensor_data": sensor_data}


@blueprint.route("/index", methods=["GET", "POST"])
@login_required
def index() -> str:
    """Index page."""
    model_list = fetch_all_models()
    scenarios = fetch_all_scenarios()

    model_name = request.form.get("model_name", None)
    scenario_description = request.form.get("scenario_description", None)
    if scenario_description == "ANY SCENARIO/NULL":
        scenario_description = None
    run_id = request.form.get("run_id", None)
    run_id = int(run_id) if run_id is not None else None
    date_from = request.form.get("startDate", None)
    date_to = request.form.get("endDate", None)
    date_to = dt.date.today() if date_to is None else dt.date.fromisoformat(date_to)
    date_from = (
        date_to - dt.timedelta(days=1)
        if date_from is None
        else dt.date.fromisoformat(date_from)
    )
    # Make the date limits into inclusive datetime limits
    dt_from = dt.datetime.combine(date_from, dt.time(hour=0, minute=0, second=0))
    dt_to = dt.datetime.combine(date_to, dt.time(hour=23, minute=59, second=59))

    if (
        request.method == "POST"
        and model_name is not None
        and dt_from is not None
        and dt_to is not None
    ):
        runs = get_runs(model_name, dt_from, dt_to, scenario_description)
        if run_id not in [r["id"] for r in runs]:
            # We don't want to show data for a run that isn't among the ones available
            # for picking by the user.
            run_id = None
    else:
        runs = None

    if request.method == "POST" and run_id is not None:
        model_data = fetch_run_data(run_id)
    else:
        model_data = None

    return render_template(
        "models.html",
        models=model_list,
        scenarios=scenarios,
        selected_model_name=model_name,
        selected_scenario_description=scenario_description,
        dt_from=dt_from,
        dt_to=dt_to,
        runs=runs,
        run_id=run_id,
        model_data=model_data,
    )
