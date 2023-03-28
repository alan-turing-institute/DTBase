"""
Module (routes.py) to handle API endpoints related to sensors
"""
from datetime import datetime, timedelta
import json

from flask import request, jsonify
from flask_login import login_required

from dtbase.backend.api.sensor import blueprint
from dtbase.core import sensors
from dtbase.core.structure import SQLA as db
from dtbase.core.utils import jsonify_query_result


@blueprint.route("/insert_sensor_type", methods=["POST"])
# @login_required
def insert_sensor_type():
    """
    Add a sensor type to the database.
    POST request should have json data (mimetype "application/json")
    containing
    {
      "name": <type_name:str>,
      "description": <type_description:str>
      "measures": [
                 {"name":<name:str>, "units":<units:str>,"datatype":<datatype:str>},
                 ...
                    ]
    }
    """

    payload = json.loads(request.get_json())
    for k in ["name", "description", "measures"]:
        if not k in payload.keys():
            raise RuntimeError(
                f"Must include '{k}' in POST request to /insert_sensor_type"
            )
    idnames = []
    db.session.begin()
    try:
        for measure in payload["measures"]:
            sensors.insert_sensor_measure(
                name=measure["name"],
                units=measure["units"],
                datatype=measure["datatype"],
                session=db.session,
            )
            idnames.append(measure["name"])
        sensors.insert_sensor_type(
            name=payload["name"],
            description=payload["description"],
            measures=idnames,
            session=db.session,
        )
    except Exception:
        db.session.rollback()
        raise
    db.session.commit()
    return jsonify(payload), 201


@blueprint.route("/insert_sensor/<type_name>", methods=["POST"])
# @login_required
def insert_sensor(type_name):
    """
    Add a sensor to the database.

    POST request should have json data (mimetype "application/json") containing
    {
      "unique_identifier": <unique identifier:str>,
    }
    by which the sensor will be distinguished from all othres, and optionally
    {
      "name": <human readable name:str>,
      "notes": <human readable notes:str>
    }
    """

    payload = json.loads(request.get_json())
    sensors.insert_sensor(type_name=type_name, **payload, session=db.session)
    db.session.commit()
    return jsonify(payload), 201


@blueprint.route("/list", methods=["GET"])
# @login_required
def list_sensors(type_name):
    """List sensors of in the database."""
    result = sensors.list_sensors(session=db.session)
    return jsonify(result), 200


@blueprint.route("/list/<type_name>", methods=["GET"])
# @login_required
def list_sensors_of_a_type(type_name):
    """List sensors of a particular type in the database."""
    result = sensors.list_sensors(type_name=type_name, session=db.session)
    return jsonify(result), 200


@blueprint.route("/list_sensor_types", methods=["GET"])
# @login_required
def list_sensor_types():
    """List sensor types in the database."""
    result = sensors.list_sensor_types(session=db.session)
    return jsonify(result), 200


@blueprint.route("/list_measures", methods=["GET"])
# @login_required
def list_sensor_measures():
    """List sensor measures in the database."""
    result = sensors.list_sensor_measures(session=db.session)
    return jsonify(result), 200


@blueprint.route("/delete_sensor/<unique_identifier>", methods=["DELETE"])
# @login_required
def delete_sensor(unique_identifier):
    """Delete a sensor from the database."""
    sensors.delete_sensor(unique_identifier=unique_identifier, session=db.session)
    db.session.commit()
    return jsonify({"message": "Sensor deleted"}), 200


@blueprint.route("/delete_sensor_type/<type_name>", methods=["DELETE"])
# @login_required
def delete_sensor_type(type_name):
    """Delete a sensor type from the database."""
    sensors.delete_sensor_type(type_name=type_name, session=db.session)
    db.session.commit()
    return jsonify({"message": "Sensor type deleted"}), 200