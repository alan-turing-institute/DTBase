import datetime as dt
import json
import re

from flask import render_template, request
from flask_login import login_required
import pandas as pd

from app.locations import blueprint
import utils
from flask import redirect, url_for, flash

@blueprint.route("/index", methods=["GET", "POST"])
@login_required
def index():
  
    if request.method == "POST":
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

        idnames = []
        for identifier in payload["identifiers"]:
            idnames.append(identifier["name"])

        idnames.sort()

     # Send a POST request to the new backend route
        data = {
                "name": payload["name"],
                "description": payload["description"],
                "identifiers": identifiers,
            }

        response = utils.backend_call("post", "/location/insert_location_schema", data)
        
        if response.status_code != 201:
                # TODO Write a more useful reaction to this.
                raise RuntimeError(f"A backend call failed: {response}")
        response_data = response.json()

        if response_data.get("status") == "success":
            flash("Location schema added successfully", "success")
        else:
            flash("Failed to add location schema", "error")

    return render_template("location_schema_form.html")
