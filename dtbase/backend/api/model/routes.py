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


@blueprint.route("/insert_model_run", methods=["POST"])
# @login_required
def insert_model_run():
    """
    Add a model run to the database.

    POST request should have json data (mimetype "application/json") containing
    {
        "model_name": <name of the model that was run:str>
        "scenario_description": <description of the scenario:str>
        "measures_and_values": <results of the run:list of dicts with the below keys>
            "measure_name": <name of the measure reported:str>
            "values": <values that the model outputs:list>
            "timestamps": <timestamps associated with the values:list>
    }
    The values can be strings, integers, floats, or booleans, depending on the measure.
    There should as many values as there are timestamps.
    Optionally the following can also be included in the paylod
    {
        "time_created": <time when this run was run, `now` by default:string>
        "create_scenario": <create the scenario if it doesn't already exist, False by
                            default:boolean>
    }
    """

    payload = json.loads(request.get_json())
    required_keys = {"model_name", "scenario_description", "measures_and_values"}
    error_response = check_keys(payload, required_keys, "/insert_model_run")
    if error_response:
        return error_response
    models.insert_model_run(**payload, session=db.session)
    db.session.commit()
    return jsonify(payload), 201
