"""
Module (routes.py) to handle endpoints related to models
"""
from datetime import datetime

from dtbase.backend.api.model import blueprint
from dtbase.backend.utils import check_keys
from dtbase.core import models
from dtbase.core.structure import SQLA as db
from flask import jsonify, request


@blueprint.route("/insert-model", methods=["POST"])
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

    payload = request.get_json()
    error_response = check_keys(payload, ["name"], "/insert-model")
    if error_response:
        return error_response

    models.insert_model(name=payload["name"], session=db.session)
    db.session.commit()
    return jsonify(payload), 201


@blueprint.route("/list-models", methods=["GET"])
# @login_required
def list_models():
    """
    List all models in the database.
    """

    result = models.list_models(session=db.session)
    return jsonify(result), 200


@blueprint.route("/delete-model", methods=["DELETE"])
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
    payload = request.get_json()
    error_response = check_keys(payload, ["name"], "/delete-model")
    if error_response:
        return error_response

    models.delete_model(model_name=payload["name"], session=db.session)
    db.session.commit()
    return jsonify({"message": "Model deleted."}), 200


@blueprint.route("/insert-model-scenario", methods=["POST"])
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
    }
    """

    payload = request.get_json()
    required_keys = ["model_name", "description"]
    error_response = check_keys(payload, required_keys, "/insert-model-scenario")
    if error_response:
        return error_response

    models.insert_model_scenario(**payload, session=db.session)
    db.session.commit()
    return jsonify(payload), 201


@blueprint.route("/list-model-scenarios", methods=["GET"])
def list_model_scenarios():
    """
    List all model scenarios in the database.
    """
    result = models.list_model_scenarios(session=db.session)
    return jsonify(result), 200


@blueprint.route("/delete-model-scenario", methods=["DELETE"])
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
    payload = request.get_json()
    required_keys = ["model_name", "description"]
    error_response = check_keys(payload, required_keys, "/delete_model_scenario")
    if error_response:
        return error_response

    models.delete_model_scenario(**payload, session=db.session)
    db.session.commit()
    return jsonify({"message": "Model scenario deleted."}), 200


@blueprint.route("/insert-model-measure", methods=["POST"])
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

    payload = request.get_json()
    required_keys = {"name", "units", "datatype"}
    error_response = check_keys(payload, required_keys, "/insert-model-measure")
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


@blueprint.route("/list-model-measures", methods=["GET"])
# @login_required
def list_models_measures():
    """
    List all model measures in the database.
    """
    model_measures = models.list_model_measures(session=db.session)
    return jsonify(model_measures), 200


@blueprint.route("/delete-model-measure", methods=["DELETE"])
# @login_required
def delete_model_measure():
    """Delete a model measure from the database.

    DELETE request should have json data (mimetype "application/json") containing
    {
        "name": <name of the measure to delete:str>
    }
    """
    payload = request.get_json()
    required_keys = {"name"}
    error_response = check_keys(payload, required_keys, "/delete-model-measure")
    if error_response:
        return error_response
    models.delete_model_measure(name=payload["name"], session=db.session)
    db.session.commit()
    return jsonify({"message": "Model measure deleted"}), 200


@blueprint.route("/insert-model-run", methods=["POST"])
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

    payload = request.get_json()
    required_keys = {"model_name", "scenario_description", "measures_and_values"}
    error_response = check_keys(payload, required_keys, "/insert-model-run")
    if error_response:
        return error_response
    models.insert_model_run(**payload, session=db.session)
    db.session.commit()
    return jsonify(payload), 201


@blueprint.route("/list-model-runs", methods=["GET"])
# @login_required
def list_model_runs():
    """
    List all model runs in the database.

    GET request should have json data (mimetype "application/json") containing
    {
        "model_name": <Name of the model to get runs for>,
        "dt_from": <Datetime string for earliest readings to get. Inclusive. In ISO 8601 format: '%Y-%m-%dT%H:%M:%S'>.  Optional, defaults to datetime.now minus one week.
        "dt_to": <Datetime string for last readings to get. Inclusive. In ISO 8601 format: '%Y-%m-%dT%H:%M:%S'>. Optional, defaults to datetime.now.
        "scenario": <The string description of the scenario to include runs for. Optional,
            by default all scenarios>,
    }

    Returns:
        A list of tuples (values, timestamp) that are the result the model run.
    """

    payload = request.get_json()
    required_keys = ["model_name"]
    error_response = check_keys(payload, required_keys, "/list-model-runs")
    if error_response:
        return error_response

    model_name = payload.get("model_name")

    dt_to = payload.get("dt_to")
    dt_from = payload.get("dt_from")
    dt_error = jsonify(
        {
            "error": "Invalid datetime format for dt_to/from. Use ISO format: '%Y-%m-%dT%H:%M:%S'"
        }
    )
    if dt_to:
        try:
            dt_to = datetime.fromisoformat(dt_to)
        except ValueError:
            return dt_error, 400
    if dt_from:
        try:
            dt_from = datetime.fromisoformat(dt_from)
        except ValueError:
            return dt_error, 400
    scenario = payload.get("scenario")

    model_runs = models.list_model_runs(
        model_name, dt_from, dt_to, scenario, session=db.session
    )
    return jsonify(model_runs), 200


@blueprint.route("/get-model-run", methods=["GET"])
# @login_required
def get_model_run():
    """
    Get the output of a model run.

    GET request should have json data (mimetype "application/json") containing
    {
        run_id: <Database ID of the model run>,
    }

    Returns:
        Dict, keyed by measure name, with values as lists of tuples (val, timestamp).
    """
    payload = request.get_json()
    required_keys = ["run_id"]
    error_response = check_keys(payload, required_keys, "/get-model-run")
    if error_response:
        return error_response

    model_run = models.get_model_run_results(**payload, session=db.session)
    converted_results = {}
    for k, v in model_run.items():
        converted_results[k] = [
            {"value": t[0], "timestamp": t[1].isoformat()} for t in v
        ]

    return jsonify(converted_results), 200


@blueprint.route("/get-model-run-sensor-measure", methods=["GET"])
# @login_required
def get_model_run_sensor_measure():
    """
    Get the sensor and sensor measure that the output of a model run should
    be compared to.

    GET request should have json data (mimetype "application/json") containing
    {
        run_id: <Database ID of the model run>,
    }

    Returns:
        Dict, with keys "sensor_unique_id", "measure_name"
    """
    payload = request.get_json()
    required_keys = ["run_id"]
    error_response = check_keys(payload, required_keys, "/get-model-run-sensor-measure")
    if error_response:
        return error_response
    result = models.get_model_run_sensor_measures(**payload)
    result_dict = {"sensor_unique_id": result[0], "measure_name": result[1]}
    return jsonify(result_dict), 200
