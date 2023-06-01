"""
A module for the main dashboard actions
"""
import datetime as dt
import json
import re

from flask import render_template, request, redirect
from flask_login import login_required
import pandas as pd

from datetime import datetime
from requests.exceptions import ConnectionError

from dtbase.webapp.app.models import blueprint
from dtbase.webapp import utils


def fetch_all_models():
    """Get all models from the database.

    Args:
        None
    Returns:
        List of dicts, one for each model
    """
    try:
        response = utils.backend_call("get", "/model/list_models")
    except ConnectionError as e:
        print("Error getting model list - is the backend running?")
        raise e
    if response.status_code != 200:
        raise RuntimeError(f"A backend call failed: {response}")
    models = response.json()
    return models


def get_run_ids(model_name):
    """
    Get the db id corresponding to all the run for the specified model.

    Args:
        model:str, the name of the model to search for
    Returns:
        run_id:int
    """
    try:
        response = utils.backend_call(
            "get", "/model/list_model_runs", {"model_name": model_name}
        )
    except ConnectionError as e:
        print("Error getting model runs - is the backend running?")
        raise e
    if response.status_code != 200:
        raise RuntimeError(f"A backend call failed: {response}")
    runs = response.json()
    if len(runs) == 0:
        return None
    run_ids = [run["id"] for run in runs]
    return run_ids


def get_run_pred_data(run_id):
    """
    Get the predicted outputs of the specified run.

    Args:
        run_id:int, database ID of the ModelRun
    Returns:
        dict, keyed by ModelMeasure, containing list of (value,timestamp) tuples.
    """
    # now get the output of the model for that run
    try:
        response = utils.backend_call("get", "/model/get_model_run", {"run_id": run_id})
    except ConnectionError as e:
        print(f"Error getting run {run_id} - is the backend running?")
        raise e
    if response.status_code != 200:
        raise RuntimeError(f"A backend call failed: {response}")
    pred_data = response.json()
    return pred_data


def get_run_sensor_data(run_id, earliest_timestamp):
    """
    Get the real data to which the prediction of a ModelRun should be compared

    Args:
       run_id: int, database ID of the ModelRun
       earliest_timestamp: str, ISO format timestamp of the earliest prediction point

    Returns:
       dict, with keys "sensor_uniq_id", "measure_name", "readings"
    """
    try:
        response = utils.backend_call(
            "get", "/model/get_model_run_sensor_measure", {"run_id": run_id}
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
            "/sensor/sensor_readings",
            payload={
                "measure_name": measure_name,
                "sensor_uniq_id": sensor_uniq_id,
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


def fetch_run_data(run_id):
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
def index():
    """Index page."""

    try:
        model_list = fetch_all_models()
        print(f"model_list is {model_list}")
    except ConnectionError:
        return redirect("/backend_not_found_error")
    if request.method == "GET":
        return render_template("models.html", models=model_list)

    else:  # POST request
        if "model_name" in request.form and not "run_id" in request.form:
            model_name = request.form["model_name"]
            run_ids = get_runs_for_model(model_name)
            return render_template("models.html", models=model_list, runs=run_ids)

    if len(model_list) > 0:
        model_name = request.form["model_name"]
        model_data = fetch_latest_run_data(model_name)
    else:
        model_name = ""
        model_data = []
    return render_template(
        "models.html",
        models=model_list,
        model_data=json.dumps(model_data),
    )
