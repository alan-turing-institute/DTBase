"""
A module for the main dashboard actions
"""
import datetime as dt
import json
import re

from flask import render_template, request
from flask_login import login_required
import pandas as pd

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
        # TODO Write a more useful reaction to this.
        raise RuntimeError(f"A backend call failed: {response}")
    models = response.json()
    return models


@blueprint.route("/index")
@login_required
def index():
    """Index page."""

    model_list = fetch_all_models()
    print(f"model_list is {model_list}")
    # Parse the various parameters we may have been passed, and load some generally
    # necessary data like list of all sensors and sensor types.
    dt_from = utils.parse_url_parameter(request, "startDate")
    dt_to = utils.parse_url_parameter(request, "endDate")

    if (
        dt_from is None
        or dt_to is None
    ):
        today = dt.datetime.today()
        dt_from = today - dt.timedelta(days=7)
        dt_to = today
        return render_template(
            "models.html",
            dt_from=dt_from,
            dt_to=dt_to,
            models=model_list,
        )

    # Convert datetime strings to objects and make dt_to run to the end of the day in
    # question.
    dt_from = dt.datetime.fromisoformat(dt_from)
    dt_to = (
        dt.datetime.fromisoformat(dt_to)
        + dt.timedelta(days=1)
        + dt.timedelta(milliseconds=-1)
    )

    return render_template(
        "models.html",
        dt_from=dt_from,
        dt_to=dt_to,
        models=model_list,
    )
