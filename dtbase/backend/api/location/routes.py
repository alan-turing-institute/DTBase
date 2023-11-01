"""
Module (routes.py) to handle API endpoints related to Locations
"""

from flask import request, jsonify, make_response

from dtbase.backend.api.location import blueprint
from dtbase.core import locations
from dtbase.core.structure import SQLA as db
from dtbase.backend.utils import check_keys

import logging

logger = logging.getLogger(__name__)


@blueprint.route("/insert-location-schema", methods=["POST"])
# @login_required
def insert_location_schema():
    """
    Add a location schema to the database.
    POST request should have json data (mimetype "application/json")
    containing
    {
      "name": <schema_name:str>,
      "description": <schema_description:str>
      "identifiers": [
                 {"name":<name:str>, "units":<units:str>,"datatype":<datatype:str>},
                 ...
                    ]
    }
    """
    try:
        payload = request.get_json()
        required_keys = ["name", "description", "identifiers"]
        error_response = check_keys(payload, required_keys, "/insert-location-schema")
        if error_response:
            return error_response
        idnames = []
        for identifier in payload["identifiers"]:
            if not identifier.get("is_existing", False):
                locations.insert_location_identifier(
                    name=identifier["name"],
                    units=identifier["units"],
                    datatype=identifier["datatype"],
                    session=db.session,
                )
            idnames.append(identifier["name"])
        # sort the idnames list, and use it to create/find a schema
        idnames.sort()
        schema_name = "-".join(idnames)
        locations.insert_location_schema(
            name=payload["name"],
            description=payload["description"],
            identifiers=idnames,
            session=db.session,
        )
        db.session.commit()
        return jsonify(payload), 201

    except Exception as e:
        # Log the error message and return a response with the error message
        logger.error("Error occurred:", str(e))
        return make_response(jsonify({"error": str(e)}), 500)


@blueprint.route("/insert-location", methods=["POST"])
# @login_required
def insert_location():
    """
    Add a location to the database, defining the schema at the same time.
    POST request should have json data (mimetype "application/json")
    containing
    {
      "identifiers": [
                 {"name":<name:str>, "units":<units:str>,"datatype":<datatype:str>},
                 ...
                    ],
      "values": [<val1>, ...]
    }
    (where values should be in the same order as identifiers).

    """

    payload = request.get_json()
    required_keys = ["identifiers", "values"]
    error_response = check_keys(payload, required_keys, "/insert-location")
    if error_response:
        return error_response

    db.session.begin()
    try:
        idnames = []
        for identifier in payload["identifiers"]:
            locations.insert_location_identifier(
                name=identifier["name"],
                units=identifier["units"],
                datatype=identifier["datatype"],
                session=db.session,
            )
            idnames.append(identifier["name"])
        # sort the idnames list, and use it to create/find a schema
        idnames.sort()
        schema_name = "-".join(idnames)
        locations.insert_location_schema(
            name=schema_name,
            description=schema_name,
            identifiers=idnames,
            session=db.session,
        )
        value_dict = {}
        for i, val in enumerate(payload["values"]):
            value_dict[payload["identifiers"][i]["name"]] = val
        value_dict["schema_name"] = schema_name
        locations.insert_location(**value_dict, session=db.session)
        db.session.commit()
        return jsonify(value_dict), 201
    except:
        db.session.rollback()
        raise


@blueprint.route("/insert-location-for-schema", methods=["POST"])
# @login_required
def insert_location_existing_schema():
    """
    Add a location to the database, given an existing schema name.
    POST request should have json data (mimetype "application/json")
    containing
    {
      "schema_name": <schema_name:str>,
      "identifier1_name": "value1",
       ...
    }
    with an identifier name and value for every identifier in the schema

    """

    payload = request.get_json()
    required_keys = ["schema_name"]
    error_response = check_keys(payload, required_keys, "/insert-location-for-schema")
    if error_response:
        return error_response
    locations.insert_location(**payload, session=db.session)
    db.session.commit()
    return jsonify(payload), 201


@blueprint.route("/list-locations", methods=["GET"])
# @login_required
def list_locations():
    """
    List location in the database, filtered by schema name.
    Optionally also filter by coordinates, if given identifiers in the payload.
    Payload should be of the form:
    {
      "schema_name": <schema_name:str>,
      "identifier1_name": <value1:float|int|str|bool>,
       ...
    }

    Returns results in the form:
    [
     { <identifier1:str>: <value1:str>, ...}, ...
    ]

    """
    payload = request.get_json()
    required_keys = ["schema_name"]
    error_response = check_keys(payload, required_keys, "/list-locations")
    if error_response:
        return error_response
    result = locations.list_locations(
        **payload,
        session=db.session,
    )
    return jsonify(result), 200


@blueprint.route("/list-location-schemas", methods=["GET"])
# @login_required
def list_location_schemas():
    """
    List location schemas in the database.

    Returns results in the form:
    [
      {
       "name": <name:str>,
       "description": <description:str>,
       "identifiers": [
          {
            "name": <identifier_name:str>,
            "units": <units:str>,
            "datatype":<"float"|"integer"|"string"|"boolean">
           }, ...
       ]
      }
    ]
    """

    result = locations.list_location_schemas(session=db.session)
    return jsonify(result), 200


@blueprint.route("/list-location-identifiers", methods=["GET"])
# @login_required
def list_location_identifiers():
    """
    List location identifiers in the database.
    """

    result = locations.list_location_identifiers(session=db.session)
    return jsonify(result), 200


@blueprint.route("/get-schema-details", methods=["GET"])
# @login_required
def get_schema_details():
    """
    Get a location schema and its identifiers from the database.

    Payload should have the form:
    {'schema_name': <schema_name:str>}

    Returns results in the form:
    {

    }
    """
    payload = request.get_json()
    schema_name = payload["schema_name"]
    result = locations.get_schema_details(schema_name, session=db.session)
    return jsonify(result), 200


@blueprint.route("/delete-location-schema", methods=["DELETE"])
# @login_required
def delete_location_schema():
    """
    Delete a location schema from the database.
    Payload should have the form:
    {'schema_name': <schema_name:str>}

    """

    # Call delete_location_schema and check that it doesn't error.
    payload = request.get_json()
    schema_name = payload["schema_name"]
    required_keys = ["schema_name"]
    error_response = check_keys(payload, required_keys, "/delete-location-schema")
    if error_response:
        return error_response
    try:
        locations.delete_location_schema(schema_name=schema_name, session=db.session)
        db.session.commit()
        return (
            jsonify(
                {
                    "status": "success",
                    "message": f"Location schema '{schema_name}' has been deleted.",
                }
            ),
            200,
        )
    except ValueError:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Location schema '{schema_name}' not found or could not be deleted.",
                }
            ),
            404,
        )


@blueprint.route("/delete-location", methods=["DELETE"])
# @login_required
def delete_location():
    """
    Delete a location with the specified schema name and coordinates.

    Payload should have the form:
    {"schema_name": <schema_name:str>}
    """
    payload = request.get_json()
    required_keys = ["schema_name"]
    error_response = check_keys(payload, required_keys, "/delete-location")
    if error_response:
        return error_response
    schema_name = payload["schema_name"]
    try:
        locations.delete_location_by_coordinates(session=db.session, **payload)
        db.session.commit()
        return jsonify({"message": "Location deleted successfully."}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
