"""
Module (routes.py) to handle API endpoints related to Locations
"""
from datetime import datetime, timedelta
import json

from flask import request, jsonify
from flask_login import login_required

from dtbase.backend.api.location import blueprint
from dtbase.core import locations
from dtbase.core.structure import SQLA as db
from dtbase.core.utils import jsonify_query_result


@blueprint.route("/insert_location_schema", methods=["POST"])
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

    payload = json.loads(request.get_json())
    for k in ["name", "description", "identifiers"]:
        if not k in payload.keys():
            raise RuntimeError(
                f"Must include '{k}' in POST request to /insert_location_schema"
            )
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
        name=payload["name"],
        description=payload["description"],
        identifiers=idnames,
        session=db.session,
    )
    db.session.commit()
    return jsonify(payload), 201


@blueprint.route("/insert_location", methods=["POST"])
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

    payload = json.loads(request.get_json())
    for k in ["identifiers", "values"]:
        if not k in payload.keys():
            raise RuntimeError(
                f"Must include '{k}' in POST request to /insert_location"
            )
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
    locations.insert_location(schema_name=schema_name, **value_dict, session=db.session)
    return jsonify(value_dict), 201


@blueprint.route("/insert_location/<schema_name>", methods=["POST"])
# @login_required
def insert_location_existing_schema(schema_name):
    """
    Add a location to the database, given an existing schema name.
    POST request should have json data (mimetype "application/json")
    containing
    {
      "identifier1_name": "value1",
       ...
    }
    for every identifier in the schema

    """

    payload = json.loads(request.get_json())

    locations.insert_location(schema_name=schema_name, **payload, session=db.session)
    db.session.commit()
    return jsonify(payload), 201


@blueprint.route("/list/<schema_name>", methods=["GET"])
# @login_required
def list_locations(schema_name):
    """
    List location in the database.
    Optionally filter by coordinates, if given a dict in the payload of the form
    {
      "identifier1_name": "value1",
       ...
    }

    """
    payload = json.loads(request.get_json(force=True)) if request.data else {}
    result = locations.list_locations(
        schema_name=schema_name,
        **payload,
        session=db.session,
    )
    return jsonify(result), 200
