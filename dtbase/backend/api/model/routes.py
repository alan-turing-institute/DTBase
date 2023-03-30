"""
Module (routes.py) to handle endpoints related to models
"""
from datetime import datetime, timedelta
import json

from flask import request, jsonify
from flask_login import login_required

from dtbase.backend.api.model import blueprint
from dtbase.backend.utils import check_keys
from dtbase.core import models
from dtbase.core.structure import SQLA as db
from dtbase.core.utils import jsonify_query_result


@blueprint.route("/insert_model", methods=["POST"])
# @login_required
def insert_model():
    """
    Add a model to the database.
    POST request should have json data (mimetype "application/json")
    containing
    {
        "name": <model_name:str>
    }
    """

    payload = json.loads(request.get_json())
    if not "name" in payload.keys():
        raise RuntimeError("Must include 'name' in POST request to /insert_model")

    models.insert_model(name=payload["name"], session=db.session)
    db.session.commit()
    return jsonify(payload), 201


@blueprint.route("/list_models", methods=["GET"])
# @login_required
def list_models():
    """
    List all models in the database.
    """
    models = models.list_models(session=db.session)
    return jsonify_query_result(models), 200


@blueprint.route("/insert_model_measure", methods=["POST"])
# @login_required
def insert_model_measure():
    """
    Add a model measure to the database.

    Model measures specify quantities that models can output, such as "mean temperature"
    or "upper 90% confidence limit for relative humidity".

    POST request should have json data (mimetype "application/json") containing
    {
        "name": <name of this measure:str>
        "units": <units in which this measure is specified:str>
        "datatype": <value type of this model measure.:str>
    }
    The datatype has to be one of "string", "integer", "float", or "boolean"
    """

    payload = json.loads(request.get_json())
    required_keys = {"name", "units", "datatype"}
    error_response = check_keys(payload, required_keys, "/insert_model_measure")
    if error_response:
        return error_response

    models.insert_model_measure(
        name=payload["name"],
        units=payload["units"],
        datatype=payload["datatype"],
        session=db.session,
    )
    db.session.commit()
    return jsonify(payload), 201


@blueprint.route("/list_model_measures", methods=["GET"])
# @login_required
def list_models_measures():
    """
    List all model measures in the database.
    """
    model_measures = models.list_model_measures(session=db.session)
    return jsonify(model_measures), 200


@blueprint.route("/delete_model_measure", methods=["DELETE"])
# @login_required
def delete_model_measure():
    """Delete a model measure from the database.

    DELETE request should have json data (mimetype "application/json") containing
    {
        "name": <name of the measure to delete:str>
    }
    """
    payload = json.loads(request.get_json())
    required_keys = {"name"}
    error_response = check_keys(payload, required_keys, "/delete_model_measure")
    if error_response:
        return error_response
    models.delete_model_measure(name=payload["name"], session=db.session)
    db.session.commit()
    return jsonify({"message": "Model measure deleted"}), 200
