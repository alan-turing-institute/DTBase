from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug.wrappers import Response

from dtbase.webapp import utils
from dtbase.webapp.app.locations import blueprint


@login_required
@blueprint.route("/new-location-schema", methods=["GET"])
def new_location_schema(form_data: str = None) -> Response:
    existing_identifiers_response = current_user.backend_call(
        "get", "/location/list-location-identifiers"
    )
    existing_identifiers = existing_identifiers_response.json()
    return render_template(
        "location_schema_form.html",
        form_data=form_data,
        existing_identifiers=existing_identifiers,
    )


@login_required
@blueprint.route("/new-location-schema", methods=["POST"])
def submit_location_schema() -> Response:
    name = request.form.get("name")
    description = request.form.get("description")
    identifier_names = request.form.getlist("identifier_name[]")
    identifier_units = request.form.getlist("identifier_units[]")
    identifier_datatypes = request.form.getlist("identifier_datatype[]")
    identifier_existing = request.form.getlist("identifier_existing[]")

    identifiers = [
        {
            "name": name,
            "units": unit,
            "datatype": datatype,
            "is_existing": is_existing == "1",
        }
        for name, unit, datatype, is_existing in zip(
            identifier_names,
            identifier_units,
            identifier_datatypes,
            identifier_existing,
        )
    ]

    form_data = {
        "name": name,
        "description": description,
        "identifiers": identifiers,
    }

    try:
        response = current_user.backend_call(
            "post", "/location/insert-location-schema", form_data
        )
    except Exception as e:
        flash(f"Error communicating with the backend: {e}", "error")
        return redirect(url_for(".new_location_schema"))

    if response.status_code == 409:
        flash(f"The schema '{name}' already exists.", "error")
    elif response.status_code != 201:
        flash(
            f"An error occurred while adding the location schema: {response}", "error"
        )
    else:
        flash("Location schema added successfully", "success")

    return redirect(url_for(".new_location_schema"))


@login_required
@blueprint.route("/new-location", methods=["GET"])
def new_location() -> str:
    response = current_user.backend_call("get", "/location/list-location-schemas")
    schemas = response.json()
    selected_schema = request.args.get("schema_name")
    return render_template(
        "location_form.html", schemas=schemas, selected_schema=selected_schema
    )


@login_required
@blueprint.route("/new-location", methods=["POST"])
def submit_location() -> Response:
    # Retrieve the name of the schema
    schema_name = request.form.get("schema")
    # Once all is said and done handling the POST request, we redirect the user here.
    redirected_destination = redirect(url_for(".new_location", schema_name=schema_name))
    # Retrieve the identifiers and values based on the schema
    payload = {"schema_name": schema_name}
    response = current_user.backend_call("get", "/location/get-schema-details", payload)
    schema = response.json()
    try:
        # Convert form values to their respective datatypes as defined in the schema
        form_data = utils.convert_form_values(schema["identifiers"], request.form)
    except ValueError as e:
        flash(str(e), "error")
        return redirected_destination

    try:
        # Send a POST request to the backend
        payload = form_data
        payload["schema_name"] = schema_name
        response = current_user.backend_call(
            "post", "/location/insert-location-for-schema", payload
        )
    except Exception as e:
        flash(f"Error communicating with the backend: {e}", "error")
        return redirected_destination

    if response.status_code == 409:
        flash("Location already exists", "error")
    elif response.status_code != 201:
        flash(
            f"An error occurred while adding the location: {response.json()}", "error"
        )
    else:
        flash("Location added successfully", "success")
    return redirected_destination


@login_required
@blueprint.route("/locations-table", methods=["GET"])
def locations_table() -> Response:
    schemas_response = current_user.backend_call(
        "get", "/location/list-location-schemas"
    )

    schemas = schemas_response.json()
    locations_for_each_schema = {}

    for schema in schemas:
        payload = {"schema_name": schema["name"]}
        locations_response = current_user.backend_call(
            "get", "/location/list-locations", payload
        )
        locations_for_each_schema[schema["name"]] = locations_response.json()

    return render_template(
        "locations_table.html",
        schemas=schemas,
        locations_for_each_schema=locations_for_each_schema,
    )
