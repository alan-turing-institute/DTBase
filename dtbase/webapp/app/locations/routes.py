import datetime as dt
import json
import re

from flask import render_template, request
from flask_login import login_required
import pandas as pd

from app.locations import blueprint
import utils
from flask import redirect, url_for, flash

@blueprint.route("/index", methods=["GET"])
@login_required
def index():
    return render_template("location_schema_form.html")

@blueprint.route("/index", methods=["POST"])
@login_required
def submit_location_schema():
    name = request.form.get("name")
    description = request.form.get("description")
    identifier_names = request.form.getlist("identifier_name[]")
    identifier_units = request.form.getlist("identifier_units[]")
    identifier_datatypes = request.form.getlist("identifier_datatype[]")

    identifiers = [
        {
            "name": identifier_name,
            "units": identifier_unit,
            "datatype": identifier_datatype
        }
        for identifier_name, identifier_unit, identifier_datatype in zip(
            identifier_names, identifier_units, identifier_datatypes
        )
    ]

    payload = {
        "name": name,
        "description": description,
        "identifiers": identifiers
    }

    # idnames = []
    # for identifier in payload["identifiers"]:
    #     idnames.append(identifier["name"])

    # idnames.sort()

    data = {
        "name": payload["name"],
        "description": payload["description"],
        "identifiers": identifiers,
    }

    existing_schemas_response = utils.backend_call("get", "/location/list_location_schemas")
    existing_schemas = existing_schemas_response.json()
    
    # check if the schema already exists
    if any(schema['name'] == name for schema in existing_schemas):
        flash(f"The schema '{name}' already exists.", "error")
        return redirect(url_for(".index"))
    
    try:
        response = utils.backend_call("post", "/location/insert_location_schema", data)
    except Exception as e:
        flash(f"Error communicating with the backend: {e}", "error")
        return redirect(url_for(".index"))

    if response.status_code != 201:
        flash(f"An error occurred while adding the location schema: {response}", "error")
    else:
        response_data = response.json()

        if response_data.get("status") == "success":
            flash("Location schema added successfully", "success")
        else:
            flash("Failed to add location schema", "error")

    return redirect(url_for(".index"))
