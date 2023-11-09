"""
A module for the main dashboard actions
"""
import json
from datetime import datetime
from typing import Any, Dict, List

from flask import redirect, render_template, request
from requests.exceptions import ConnectionError
from werkzeug.wrappers import Response

from dtbase.webapp import utils
from dtbase.webapp.app.models import blueprint


def fetch_all_models() -> List[dict]:
    """Get all models from the database.

    Args:
        None
    Returns:
        List of dicts, one for each model
    """
    try:
        response = utils.backend_call("get", "/model/list-models")
    except ConnectionError as e:
        print("Error getting model list - is the backend running?")
        raise e
    if response.status_code != 200:
        raise RuntimeError(f"A backend call failed: {response}")
    models = response.json()
    return models


def get_run_ids(model_name: str) -> List[int]:
    """
    Get the db id corresponding to all the run for the specified model.

    Args:
        model:str, the name of the model to search for
    Returns:
        run_id:int
    """
    try:
        response = utils.backend_call(
            "get", "/model/list-model-runs", {"model_name": model_name}
        )
    except ConnectionError as e:
        print("Error getting model runs - is the backend running?")
        raise e
    if response.status_code != 200:
        raise RuntimeError(f"A backend call failed: {response}")
    runs = response.json()
    if len(runs) == 0:
        return []
    run_ids = [run["id"] for run in runs]
    return run_ids


def get_run_pred_data(run_id: int) -> Dict[str, Any]:
    """
    Get the predicted outputs of the specified run.

    Args:
        run_id:int, database ID of the ModelRun
    Returns:
        dict, keyed by ModelMeasure, containing list of dicts
        {"timestamp":<ts:str>, "value": <val:int|float|str|bool>}
    """
    # now get the output of the model for that run
    try:
        response = utils.backend_call("get", "/model/get-model-run", {"run_id": run_id})
    except ConnectionError as e:
        print(f"Error getting run {run_id} - is the backend running?")
        raise e
    if response.status_code != 200:
        raise RuntimeError(f"A backend call failed: {response}")
    pred_data = response.json()
    return pred_data


def get_run_sensor_data(run_id: int, earliest_timestamp: str) -> Dict[str, Any]:
    """
    Get the real data to which the prediction of a ModelRun should be compared

    Args:
       run_id: int, database ID of the ModelRun
       earliest_timestamp: str, ISO format timestamp of the earliest prediction point

    Returns:
       dict, with keys "sensor_uniq_id", "measure_name", "readings", where "readings" is
       a list of (value, timestamp) tuples.
    """
    try:
        response = utils.backend_call(
            "get", "/model/get-model-run-sensor-measure", {"run_id": run_id}
        )
    except ConnectionError as e:
        print(f"Error getting run sensor data for {run_id} - is backend running?")
        raise e
    if response.status_code != 200:
        raise RuntimeError(f"A backend call failed: {response}")
    measure_name = response.json()["measure_name"]
    sensor_uniq_id = response.json()["sensor_unique_id"]
    dt_from = earliest_timestamp
    dt_to = datetime.now().isoformat()
    try:
        response = utils.backend_call(
            "get",
            "/sensor/sensor-readings",
            payload={
                "measure_name": measure_name,
                "unique_identifier": sensor_uniq_id,
                "dt_from": dt_from,
                "dt_to": dt_to,
            },
        )
    except ConnectionError as e:
        print(
            f"Error getting sensor readings for {sensor_uniq_id} - is backend running?"
        )
        raise e
    if response.status_code != 200:
        raise RuntimeError(f"A backend call failed: {response}")
    readings = response.json()
    return {
        "sensor_uniq_id": sensor_uniq_id,
        "measure_name": measure_name,
        "readings": readings,
    }


def fetch_run_data(run_id: int) -> Dict[str, Any]:
    """
    Fetch all the info for the latest prediction run for a given model.

    Args:
       run_id:int, identifier of the model run.
    Returns:
       dict, with keys "pred_data", "sensor_data".
    """
    pred_data = get_run_pred_data(run_id)
    # find the earliest time in the predicted data
    earliest_timestamp = pred_data[list(pred_data.keys())[0]][0]["timestamp"]
    sensor_data = get_run_sensor_data(run_id, earliest_timestamp)
    return {"pred_data": pred_data, "sensor_data": sensor_data}


@blueprint.route("/index", methods=["GET", "POST"])
# @login_required
def index() -> Response:
    """Index page."""
    model_list = []
    run_ids = []
    try:
        model_list = fetch_all_models()
        print(f"model_list is {model_list}")
    except ConnectionError:
        return redirect("/backend_not_found_error")
    if request.method == "GET":
        print("GET REQUEST")
        return render_template("models.html", models=model_list, model_data={})

    else:  # POST request
        print(f"POST REQUEST {request.form}")
        if "model_name" in request.form and "run_id" not in request.form:
            model_name = request.form["model_name"]
            run_ids = get_run_ids(model_name)
            print(f"Got run_ids {run_ids}")
            return render_template(
                "models.html",
                models=model_list,
                selected_model_name=model_name,
                run_ids=run_ids,
                model_data={},
            )
        elif "model_name" in request.form and "run_id" in request.form:
            model_name = request.form["model_name"]
            run_id = request.form["run_id"]
            model_data = fetch_run_data(run_id)
            return render_template(
                "models.html",
                models=model_list,
                run_ids=run_ids,
                selected_model_name=model_name,
                run_id=run_id,
                model_data=json.dumps(model_data),
            )
        # TODO What to do if neither of the above is true?
