import json

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required

from dtbase.webapp.app.locations import blueprint
from dtbase.webapp import utils


@login_required
@blueprint.route("/new_location_schema", methods=["GET"])
def new_location_schema(form_data=None):
    existing_identifiers_response = utils.backend_call(
        "get", "/location/list_location_identifiers"
    )
    existing_identifiers = existing_identifiers_response.json()
    return render_template(
        "location_schema_form.html",
        form_data=form_data,
        existing_identifiers=existing_identifiers,
    )


@login_required
@blueprint.route("/new_location_schema", methods=["POST"])
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
            "datatype": identifier_datatype,
        }
        for identifier_name, identifier_unit, identifier_datatype in zip(
            identifier_names, identifier_units, identifier_datatypes
        )
    ]

    form_data = {
        "name": name,
        "description": description,
        "identifiers": identifiers,
    }

    # check if the schema already exists
    existing_schemas_response = utils.backend_call(
        "get", "/location/list_location_schemas"
    )
    existing_schemas = existing_schemas_response.json()
    if any(schema["name"] == name for schema in existing_schemas):
        flash(f"The schema '{name}' already exists.", "error")
        return new_location_schema(form_data=form_data)

    # check if any of the identifiers already exist
    existing_identifiers_response = utils.backend_call(
        "get", "/location/list_location_identifiers"
    )

    existing_identifiers = existing_identifiers_response.json()

    for idf in identifiers:
        for idf_ex in existing_identifiers:
            # if a new identifier has the same name as an existing one, throw an error
            if (idf["name"] == idf_ex["name"]) & (idf != idf_ex):
                flash(
                    f"An identifier with the name '{idf['name']}' already exists.",
                    "error",
                )
        return new_location_schema(form_data=form_data)

    try:
        response = utils.backend_call(
            "post", "/location/insert_location_schema", form_data
        )
    except Exception as e:
        flash(f"Error communicating with the backend: {e}", "error")
        return redirect(url_for(".new_location_schema"))

    if response.status_code != 201:
        flash(
            f"An error occurred while adding the location schema: {response}", "error"
        )
    else:
        flash("Location schema added successfully", "success")

    return redirect(url_for(".new_location_schema"))
