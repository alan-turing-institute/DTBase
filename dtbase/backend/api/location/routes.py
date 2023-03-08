"""
Module (routes.py) to handle API endpoints related to Locations
"""
from datetime import datetime, timedelta
import json

from flask import request, jsonify
from flask_login import login_required

from dtbase.core.structure import SQLA as db
from dtbase.core.utils import jsonify_query_result
from dtbase.backend.api.location import blueprint

from dtbase.backend import locations


@blueprint.route("/insert_location", methods=["POST"])
# @login_required
def insert_location():
    """
    Add a location to the database.
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
            raise RuntimeError(f"Must include '{k}' in POST request to /insert_location")
    idnames = []
    for identifier in payload["identifiers"]:
        locations.insert_location_identifier(
            name = identifier["name"],
            units = identifier["units"],
            datatype = identifier["datatype"],
            session = db.session
        )
        idnames.append(identifier["name"])
    # sort the idnames list, and use it to create/find a schema
    idnames.sort()
    schema_name = "-".join(idnames)
 #   locations.insert_location_schema(
 #       name = schema_name,
 #       description = schema_name,
 #       identifiers = payload["identifiers"],
 #       session = db.session
 #   )
    value_dict = {}
    for i, val in enumerate(payload["values"]):
        value_dict[payload["identifiers"][i]["name"]] = val
    print(f"NICK!!! value_dict {value_dict}")
#    locations.insert_location(
#        schema_name = schema_name,
#        **value_dict,
#        session = db.session
#    )
    return jsonify(value_dict), 200
