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