"""
A module for the main dashboard actions
"""
import datetime as dt
import json
import re

from flask import render_template, request
from flask_login import login_required
import pandas as pd

from datetime import datetime

from app.models import blueprint
import utils

def fetch_all_models():
    """Get all models from the database.

    Args:
        None
    Returns:
        List of dicts, one for each model
    """
    response = utils.backend_call("get", "/model/list_models")
    if response.status_code != 200:
        raise RuntimeError(f"A backend call failed: {response}")
    models = response.json()
    return models


def get_latest_run_id(model_name):
    """
    Get the db id corresponding to the latest run for the specified model.

    Args:
        model:str, the name of the model to search for
    Returns:
        run_id:int
    """
    response = utils.backend_call(
        "get",
        "/model/list_model_runs",
        {"model_name": model_name}
    )
    if response.status_code != 200:
        raise RuntimeError(f"A backend call failed: {response}")
    runs = response.json()
    if len(runs) == 0:
        return None
    run_id = runs[-1]["id"]
    return run_id


def get_run_pred_data(run_id):
    """
    Get the predicted outputs of the specified run.

    Args:
        run_id:int, database ID of the ModelRun
    Returns:
        dict, keyed by ModelMeasure, containing list of (value,timestamp) tuples.
    """
    # now get the output of the model for that run
    response = utils.backend_call(
        "get",
        "/model/get_model_run",
        {"run_id": run_id}
    )
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
    response = utils.backend_call(
        "get",
        "/model/get_model_run_sensor_measure",
        {"run_id": run_id}
    )
    if response.status_code != 200:
        raise RuntimeError(f"A backend call failed: {response}")
    measure_name = response.json()["measure_name"]
    sensor_uniq_id = response.json()["sensor_unique_id"]
    dt_from = earliest_timestamp
    dt_to = datetime.now().isoformat()
    response = utils.backend_call(
        "get",
        "/sensor/sensor_readings",
        payload = {
            "measure_name": measure_name,
            "sensor_uniq_id": sensor_uniq_id,
            "dt_from": dt_from,
            "dt_to": dt_to
        }
    )
    if response.status_code != 200:
        raise RuntimeError(f"A backend call failed: {response}")
    readings = response.json()
    return {
        "sensor_uniq_id": sensor_uniq_id,
        "measure_name": measure_name,
        "readings": readings
    }

def fetch_latest_run_data(model_name):
    """
    Fetch all the info for the latest prediction run for a given model.

    Args:
       model_name:str, the name of the Model.
    Returns:
       dict, with keys "pred_data", "sensor_data".
    """
    run_id = get_latest_run_id(model_name)
    pred_data = get_run_pred_data(run_id)
    # find the earliest time in the predicted data
    earliest_timestamp = pred_data[list(pred_data.keys())[0]][0]["timestamp"]
    sensor_data = get_run_sensor_data(run_id, earliest_timestamp)
    return {"pred_data": pred_data, "sensor_data": sensor_data}


@blueprint.route("/index")
#@login_required
def index():
    """Index page."""

    model_list = fetch_all_models()
    print(f"model_list is {model_list}")

    # for now just show results for the latest run of the first model
    model_name = model_list[0]["name"]

    model_data = fetch_latest_run_data(model_name)

    return render_template(
        "models.html",
        models=model_list,
        model_data=json.dumps(model_data),
    )
