"""
A module for the main dashboard actions
"""
import datetime as dt
import json
import re
from typing import Any, Dict, List

import pandas as pd
from dateutil.parser import parse
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug.wrappers import Response

from dtbase.core.constants import CONST_MAX_RECORDS
from dtbase.frontend import utils
from dtbase.frontend.app.sensors import blueprint


def fetch_all_sensor_types() -> List[dict]:
    """Get all sensor types from the database.
    Args:
        None
    Returns:
        List of dictionaries, one for each sensor type, including a dict of measures for
            each
    """
    try:
        response = current_user.backend_call("get", "/sensor/list-sensor-types")
    # TODO Can we catch a more specific exception here?
    except Exception:
        raise RuntimeError("No response from backend")
    if response.status_code != 200:
        raise RuntimeError(f"A backend call failed: {response}")
    sensor_types = response.json()
    return sensor_types


def fetch_all_sensors(sensor_type: str) -> List[dict[str, Any]]:
    """Get all sensors of a given sensor type from the database.
    Args:
        sensor_type: The name of the sensor type.
    Returns:
        List of dictionaries, one for each sensor.
    """
    if not sensor_type:
        return []
    payload = {"type_name": sensor_type}
    response = current_user.backend_call("post", "/sensor/list-sensors", payload)
    if response.status_code != 200:
        # TODO Write a more useful reaction to this.
        raise RuntimeError(f"A backend call failed: {response}")
    sensors = response.json()
    return sensors


def fetch_sensor_data(
    dt_from: dt.datetime | str,
    dt_to: dt.datetime | str,
    measures: List[dict],
    sensor_ids: List[str],
) -> Dict[str, pd.DataFrame]:
    """Get the data from a given sensor and measure, in a given time period.
    Args:
        dt_from: Datetime from, either as a datetime object or as an ISO format string
        dt_to: Datetime to, either as a datetime object or as an ISO format string
        measures: List of dicts, each with keys "name", "datatype", "units" for a
            measure.
        sensor_ids: List of strings, Unique IDs of sensors to get data for
    Returns:
        Dictionary with keys being sensor IDs and values being pandas DataFrames of
        data, with columns for each measure and for timestamp.
    """
    result = {}
    if isinstance(dt_from, dt.datetime):
        dt_from = dt_from.isoformat()
    if isinstance(dt_to, dt.datetime):
        dt_to = dt_to.isoformat()
    for sensor_id in sensor_ids:
        measure_readings_list = []
        for measure in measures:
            payload = {
                "dt_from": dt_from,
                "dt_to": dt_to,
                "measure_name": measure["name"],
                "unique_identifier": sensor_id,
            }
            response = current_user.backend_call(
                "post", "/sensor/sensor-readings", payload
            )
            if response.status_code != 200:
                # TODO Write a more useful reaction to this.
                raise RuntimeError(f"A backend call failed: {response}")
            readings = response.json()
            index = [x["timestamp"] for x in readings]
            values = [x["value"] for x in readings]
            index = list(map(parse, index))
            series = pd.Series(data=values, index=index, name=measure["name"])
            measure_readings_list.append(series)
        df = pd.concat(measure_readings_list, axis=1)
        df = df.sort_index().reset_index(names="timestamp")
        result[sensor_id] = df
    return result


@blueprint.route("/time-series-plots", methods=["GET", "POST"])
@login_required
def time_series_plots() -> Response:
    """Time-series plots of sensor data"""
    # Parse the various parameters we may have been passed, and load some generally
    # necessary data like list of all sensors and sensor types.
    dt_from = utils.parse_url_parameter(request, "startDate")
    dt_to = utils.parse_url_parameter(request, "endDate")
    sensor_ids = utils.parse_url_parameter(request, "sensorIds")
    if sensor_ids is not None:
        # sensor_ids is passed as a comma-separated (or semicolon, although those aren't
        # currently used) string, split it into a list of ids.
        sensor_ids = tuple(re.split(r"[;,]+", sensor_ids.rstrip(",;")))
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
            "time_series_plots.html",
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
    dt_from = parse(dt_from)
    dt_to = parse(dt_to) + dt.timedelta(days=1) + dt.timedelta(milliseconds=-1)

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
        "time_series_plots.html",
        sensor_type=sensor_type_name,
        sensor_types=sensor_types,
        all_sensors=all_sensors,
        sensor_ids=sensor_ids,
        dt_from=dt_from,
        dt_to=dt_to,
        data=data_dict,
        measures=measures,
    )


# Plot sensor readings in responsive datatables
@blueprint.route("/readings", methods=["GET", "POST"])
@login_required
def sensor_readings() -> Response | str:
    """
    Render tables of readings for a selected sensor type.

    The html contains dropdowns for 'sensor_type' and 'sensor', where
    the list for the sensor dropdown depends on the selected sensor_type.
    Only when the sensor is selected will the date selector be available,
    and only when start and end dates are selected will the
    datatable be populated.
    """
    sensor_types = fetch_all_sensor_types()
    sensor_type_names = [st["name"] for st in sensor_types]

    sensor_ids_by_type = {
        st: [s["unique_identifier"] for s in fetch_all_sensors(st)]
        for st in sensor_type_names
    }

    dt_to = request.form.get("endDate", dt.date.today().isoformat())
    dt_from = request.form.get("startDate", dt.date.today().isoformat())
    sensor_type = request.form.get("sensor_type", None)
    sensor_id = request.form.get("sensor", None)

    if (
        dt_from is not None
        and dt_to is not None
        and sensor_type is not None
        and sensor_id is not None
        and sensor_id in sensor_ids_by_type[sensor_type]
    ):
        # We have everything we need to get some actual data.
        measures = next(s["measures"] for s in sensor_types if s["name"] == sensor_type)
        measure_names = [m["name"] for m in measures]
        # get the data for that sensor - initially a dict of DataFrames
        sensor_data = fetch_sensor_data(dt_from, dt_to, measures, [sensor_id])
        # get the DataFrame for this sensor, and convert to dict
        sensor_data = sensor_data[sensor_id]
        sensor_data["timestamp"].map(lambda x: x.isoformat())
        sensor_data = sensor_data.to_dict("records")
    else:
        measure_names = None
        sensor_data = None
    return render_template(
        "readings.html",
        sensor_types=sensor_type_names,
        selected_sensor_type=sensor_type,
        sensor_ids_by_type=sensor_ids_by_type,
        selected_sensor=sensor_id,
        measure_names=measure_names,
        sensor_data=sensor_data,
        dt_from=dt_from,
        dt_to=dt_to,
        num_records=CONST_MAX_RECORDS,
    )


@blueprint.route("/add-sensor-type", methods=["GET"])
@login_required
def new_sensor_type(form_data: str = None) -> Response:
    """
    Form to add a new SensorType, with associated measures.
    """
    existing_measures_response = current_user.backend_call(
        "get", "/sensor/list-measures"
    )
    existing_measures = existing_measures_response.json()
    return render_template(
        "sensor_type_form.html",
        form_data=form_data,
        existing_measures=existing_measures,
    )


@blueprint.route("/add-sensor-type", methods=["POST"])
@login_required
def submit_sensor_type() -> Response:
    """
    Send a POST request to add a new sensor type to the database.
    """
    name = request.form.get("name")
    description = request.form.get("description")
    measure_names = request.form.getlist("measure_name[]")
    measure_units = request.form.getlist("measure_units[]")
    measure_datatypes = request.form.getlist("measure_datatype[]")
    measure_existing = request.form.getlist("measure_existing[]")
    measures = [
        {
            "name": measure_name,
            "units": measure_unit,
            "datatype": measure_datatype,
            "is_existing": measure_is_existing == "1",
        }
        for measure_name, measure_unit, measure_datatype, measure_is_existing in zip(
            measure_names,
            measure_units,
            measure_datatypes,
            measure_existing,
        )
    ]

    form_data = {
        "name": name,
        "description": description,
        "measures": measures,
    }

    # check if the sensor type already exists
    existing_types_response = current_user.backend_call(
        "get", "/sensor/list-sensor-types"
    )
    existing_types = existing_types_response.json()
    if any(sensor_type["name"] == name for sensor_type in existing_types):
        flash(f"The sensor type '{name}' already exists.", "error")
        return new_sensor_type(form_data=form_data)

    # check if any of the measures already exist
    existing_measures_response = current_user.backend_call(
        "get", "/sensor/list-measures"
    )

    existing_measures = existing_measures_response.json()
    # new measures shouldn't have the same name as existing measures
    for idf in measures:
        if not idf["is_existing"]:
            for idf_ex in existing_measures:
                if idf["name"] == idf_ex["name"]:
                    flash(
                        f"A measure with the name '{idf['name']}' already exists.",
                        "error",
                    )
                    return new_sensor_type(form_data=form_data)

    response = current_user.backend_call(
        "post", "/sensor/insert-sensor-type", form_data
    )

    if response.status_code != 201:
        flash(f"An error occurred while adding the sensor type: {response}", "error")
    else:
        flash("Sensor type added successfully", "success")

    return redirect(url_for(".new_sensor_type"))


@login_required
@blueprint.route("/add-sensor", methods=["GET"])
def new_sensor() -> Response:
    response = current_user.backend_call("get", "/sensor/list-sensor-types")
    sensor_types = response.json()
    return render_template("sensor_form.html", sensor_types=sensor_types)


@login_required
@blueprint.route("/add-sensor", methods=["POST"])
def submit_sensor() -> Response:
    form_data = request.form
    payload = {}
    for k, v in form_data.items():
        if k == "sensor_type":
            payload["type_name"] = v
        else:
            payload[k] = v

    # Check if the unique identifier already exists
    sensor_type_response = current_user.backend_call("get", "/sensor/list-sensor-types")
    for sensor_type in sensor_type_response.json():
        payload_check = {"type_name": sensor_type["name"]}
        sensors_list = current_user.backend_call(
            "post", "/sensor/list-sensors", payload_check
        )
        for sensor in sensors_list.json():
            if sensor["unique_identifier"] == payload["unique_identifier"]:
                flash(
                    f"Sensor with unique identifier {payload['unique_identifier']} "
                    "already exists",
                    "error",
                )
                return redirect(url_for(".new_sensor"))

    try:
        # Send a POST request to the backend
        response = current_user.backend_call("post", "/sensor/insert-sensor", payload)
    except Exception as e:
        flash(f"Error communicating with the backend: {e}", "error")
        return redirect(url_for(".new_sensor"))

    if response.status_code != 201:
        flash(f"An error occurred while adding the sensor: {response.json()}", "error")
        return redirect(url_for(".new_sensor"))

    flash("Sensor added successfully", "success")
    return redirect(url_for(".new_sensor"))


@login_required
@blueprint.route("/sensor-list", methods=["GET"])
def sensor_list_table() -> Response:
    sensor_type_response = current_user.backend_call("get", "/sensor/list-sensor-types")

    sensor_types = sensor_type_response.json()
    sensors_for_each_type = {}

    for sensor_type in sensor_types:
        payload = {"type_name": sensor_type["name"]}
        sensors_response = current_user.backend_call(
            "post", "/sensor/list-sensors", payload
        )

        sensors_for_each_type[sensor_type["name"]] = sensors_response.json()

    return render_template(
        "sensor_list_table.html",
        sensor_types=sensor_types,
        sensors_for_each_type=sensors_for_each_type,
    )


@login_required
@blueprint.route("/sensor-edit-form", methods=["GET", "POST", "DELETE"])
def sensor_edit_form() -> Response:
    payload = {}

    if request.method == "POST":
        unique_identifier = request.args.get("unique_identifier")
        payload["unique_identifier"] = unique_identifier
        for k, v in request.form.items():
            payload[k] = v
        response = current_user.backend_call("post", "/sensor/edit-sensor", payload)
        if response.status_code == 200:
            flash("Sensor edited successfully", "success")
        return "", 200

    if request.method == "DELETE":
        unique_identifier = request.args.get("unique_identifier")
        payload["unique_identifier"] = unique_identifier
        response = current_user.backend_call("post", "/sensor/delete-sensor", payload)
        if response.status_code == 200:
            flash("Sensor deleted successfully", "success")
        return "", 200

    all_args = request.args
    return render_template("sensor_edit_form.html", all_args=all_args)
