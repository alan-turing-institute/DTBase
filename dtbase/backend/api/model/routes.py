"""
Module (routes.py) to handle endpoints related to models
"""
from datetime import datetime, timedelta
import json

from flask import request, jsonify
from flask_login import login_required

from dtbase.backend.api.model import blueprint
from dtbase.core import models
from dtbase.core.structure import SQLA as db
from dtbase.core.utils import jsonify_query_result
from dtbase.backend.utils import check_keys

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
    error_response = check_keys(payload, ["name"], "/insert_model")
    if error_response:
        return error_response
    
    models.insert_model(name=payload["name"], session=db.session)
    db.session.commit()
    return jsonify(payload), 201


@blueprint.route("/list_models", methods=["GET"])
# @login_required
def list_models():
    """
    List all models in the database.
    """
    result = models.list_models(session=db.session)
    return jsonify(result), 200
    

@blueprint.route("/delete_model", methods=["DELETE"])
# @login_required
def delete_model():
    """
    Delete a model from the database
    DELETE request should have json data (mimetype "application/json")
    containing
    {
        "name": <model_name:str>
    }
    """
    payload = json.loads(request.get_json())
    error_response = check_keys(payload, ["name"], "/delete_model")
    if error_response:
        return error_response
    
    models.delete_model(model_name=payload["name"], session=db.session)
    db.session.commit()
    return jsonify({"message": "Model deleted."}), 200


@blueprint.route("/insert_model_scenario", methods=["POST"])
def insert_model_scenario():
    """
    Insert a model scenario into the database.
    
    A model scenario specifies parameters for running a model. It is always tied to a
    particular model. It comes with a free form text description only (can also be
    null).
    
    POST request should have json data (mimetype "application/json")
    containing
    {
        "model_name": <model_name:str>,
        "description": <description:str> (can be None/null),
        "session": <session:sqlalchemy.orm.session.Session> (optional)
    """
    
    payload = json.loads(request.get_json())
    required_keys = ["model_name", "description"]
    error_response = check_keys(payload, required_keys, "/insert_model")
    if error_response:
        return error_response
    
    models.insert_model_scenario(**payload, session=db.session)
    db.session.commit()
    return jsonify(payload), 201
    
    
@blueprint.route("/list_model_scenarios", methods=["GET"])
def list_model_scenarios():
    """
    List all model scenarios in the database.
    """
    result = models.list_model_scenarios(session=db.session)
    return jsonify(result), 200


@blueprint.route("/delete_model_scenario", methods=["DELETE"])
def delete_model_scenario():
    """
    Delete a model scenario from the database
    DELETE request should have json data (mimetype "application/json")
    containing
    {
        "model_name": <model_name:str>,
        "description": <description:str>
    }
    """
    payload = json.loads(request.get_json())
    required_keys = ["model_name", "description"]
    error_response = check_keys(payload, required_keys, "/delete_model_scenario")
    if error_response:
        return error_response
    
    models.delete_model_scenario(**payload, session=db.session)
    db.session.commit()
    return jsonify({"message": "Model scenario deleted."}), 200




