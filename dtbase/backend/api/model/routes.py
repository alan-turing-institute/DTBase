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
   

    