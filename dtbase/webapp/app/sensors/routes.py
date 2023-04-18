"""
A module for the main dashboard actions
"""
import datetime as dt
import json
import re

from flask import render_template, request
from flask_login import login_required
import pandas as pd

from app.home import blueprint
import utils



@blueprint.route("/index")
@login_required
def index():
    """Index page."""
    sensor_types = fetch_all_sensor_types()
    sensor_type_name = utils.parse_url_parameter(request, "sensorType")
    if sensor_types:
        if sensor_type_name is None:
            # By default, just pick the first sensor type in the list.
            sensor_type_name = sensor_types[0]["name"]
    else:
        sensor_type_name = None
    all_sensors = fetch_all_sensors(sensor_type_name)

    # If we don't have the information necessary to plot data for sensors, just render
    # the selector version of the page.
    is_valid_sensor_type = sensor_type_name is not None and sensor_type_name in [
        s["name"] for s in sensor_types
    ]
    if (
        dt_from is None
        or dt_to is None
        or sensor_ids is None
        or not is_valid_sensor_type
    ):
        today = dt.datetime.today()
        dt_from = today - dt.timedelta(days=7)
        dt_to = today
        return render_template(
            "sensors.html",
            sensor_type=sensor_type_name,
            sensor_types=sensor_types,
            all_sensors=all_sensors,
            sensor_ids=sensor_ids,
            dt_from=dt_from,
            dt_to=dt_to,
            data=dict(),
            measures=[],
        )

    # Convert datetime strings to objects and make dt_to run to the end of the day in
    # question.
    dt_from = dt.datetime.fromisoformat(dt_from)
    dt_to = (
        dt.datetime.fromisoformat(dt_to)
        + dt.timedelta(days=1)
        + dt.timedelta(milliseconds=-1)
    )

    # Get all the sensor measures for this sensor type.
    measures = next(
        s["measures"] for s in sensor_types if s["name"] == sensor_type_name
    )
    sensor_data = fetch_sensor_data(dt_from, dt_to, measures, sensor_ids)

    # Convert the sensor data to an easily digestible version for Jinja.
    # You may wonder, why we first to_json, and then json.loads. That's just to have
    # the data in a nice nested dictionary that a final json.dumps can deal with.
    data_dict = {
        k: json.loads(v.to_json(orient="records", date_format="iso"))
        for k, v in sensor_data.items()
    }
    return render_template(
        "sensors.html",
        sensor_type=sensor_type_name,
        sensor_types=sensor_types,
        all_sensors=all_sensors,
        sensor_ids=sensor_ids,
        dt_from=dt_from,
        dt_to=dt_to,
        data=data_dict,
        measures=measures,
    )
