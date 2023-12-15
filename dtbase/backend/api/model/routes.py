"""
Module (routes.py) to handle endpoints related to models
"""
from datetime import datetime
from typing import Tuple

from flask import Response, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError

from dtbase.backend.api.model import blueprint
from dtbase.backend.utils import check_keys
from dtbase.core import models
from dtbase.core.exc import RowMissingError
from dtbase.core.structure import db


@blueprint.route("/insert-model", methods=["POST"])
@jwt_required()
def insert_model() -> Tuple[Response, int]:
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
    try:
        models.insert_model(name=payload["name"], session=db.session)
    except IntegrityError:
        return jsonify({"message": "Model exists already"}), 409
    db.session.commit()
    return jsonify({"message": "Model inserted"}), 201


@blueprint.route("/list-models", methods=["GET"])
@jwt_required()
def list_models() -> Tuple[Response, int]:
    """
    List all models in the database.
    """

    result = models.list_models()
    return jsonify(result), 200


@blueprint.route("/delete-model", methods=["DELETE"])
@jwt_required()
def delete_model() -> Tuple[Response, int]:
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
@jwt_required()
def insert_model_scenario() -> Tuple[Response, int]:
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
@jwt_required()
def list_model_scenarios() -> Tuple[Response, int]:
    """
    List all model scenarios in the database.

    Returns JSON of the format
    [
        {
            "id": <id:int>,
            "model_id": <model_id:int>,
            "description": <description:str|None|null>
        },
        ...
    ]
    """
    result = models.list_model_scenarios()
    return jsonify(result), 200


@blueprint.route("/delete-model-scenario", methods=["DELETE"])
@jwt_required()
def delete_model_scenario() -> Tuple[Response, int]:
    """
    Delete a model scenario from the database.

    DELETE request should have json data (mimetype "application/json") containing
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
@jwt_required()
def insert_model_measure() -> Tuple[Response, int]:
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
@jwt_required()
def list_models_measures() -> Tuple[Response, int]:
    """
    List all model measures in the database.
    """
    model_measures = models.list_model_measures()
    return jsonify(model_measures), 200


@blueprint.route("/delete-model-measure", methods=["DELETE"])
@jwt_required()
def delete_model_measure() -> Tuple[Response, int]:
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
@jwt_required()
def insert_model_run() -> Tuple[Response, int]:
    """
    Add a model run to the database.

    POST request should have json data (mimetype "application/json") containing
    {
        "model_name": <name of the model that was run:str>,
        "scenario_description": <description of the scenario:str>,
        "measures_and_values": [
            {
                "measure_name": <name of the measure reported:str>,
                "values": <values that the model outputs:list>,
                "timestamps": <timestamps associated with the values:list>
            }
            ...
        ]
    }
    The measures_and_values, which holds the results of the model should have as many
    entries as this model records measures. The values can be strings, integers, floats,
    or booleans, depending on the measure. There should as many values as there are
    timestamps.

    Optionally the following can also be included in the paylod
    {
        "time_created": <time when this run was run, `now` by default:string>,
        "create_scenario": <create the scenario if it doesn't already exist, False by
                            default:boolean>,
        "sensor_unique_id": <id for the associated sensor:string>,
        "sensor_measure": {
            "name": <name of the associated sensor measure:string>,
            "units": <name of the associated sensor measure:string>
        }
    }

    Returns status code 201 on success.
    """

    payload = request.get_json()
    required_keys = {"model_name", "scenario_description", "measures_and_values"}
    error_response = check_keys(payload, required_keys, "/insert-model-run")
    if error_response:
        return error_response
    models.insert_model_run(**payload, session=db.session)
    db.session.commit()
    return jsonify({"message": "Model run successfully inserted"}), 201


@blueprint.route("/list-model-runs", methods=["GET"])
@jwt_required()
def list_model_runs() -> Tuple[Response, int]:
    """
    List all model runs in the database.

    GET request should have json data (mimetype "application/json") containing
    {
        "model_name": <Name of the model to get runs for:string>,
        "dt_from": <Datetime for earliest readings to get. Inclusive. Optional, defaults
            to now minus one week.:string>
        "dt_to": <Datetime for last readings to get. Inclusive. Optional, defaults to
            now.:string>
        "scenario": <The string description of the scenario to include runs for.
            Optional, by default all scenarios.:string>,
    }
    Both dt_from and dt_to should be in ISO 8601 format: '%Y-%m-%dT%H:%M:%S'.

    On success, returns 200 with
    [
        {
            "id": <database id of the model run:int>,
            "model_id": <database id of the model:int>,
            "model_name": <name of the model:str>,
            "scenario_id": <database id of the scenario:int>,
            "scenario_description": <description of the scenario:str>,
            "time_created": <time when this run was created:str in ISO 8601>,
            "sensor_unique_id": <unique identifier of the associated sensor:str or
                null>,
            "sensor_measure": {
                "name": <name of the associated sensor measure:str or null>,
                "units": <units of the associated sensor measure:str or null>
            }
        }
        ...
    ]
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
            "error": "Invalid datetime format for dt_to/from. "
            "Use ISO format: '%Y-%m-%dT%H:%M:%S'"
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

    model_runs = models.list_model_runs(model_name, dt_from, dt_to, scenario)
    for run in model_runs:
        run["time_created"] = run["time_created"].isoformat()
    return jsonify(model_runs), 200


@blueprint.route("/get-model-run", methods=["GET"])
@jwt_required()
def get_model_run() -> Tuple[Response, int]:
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

    model_run = models.get_model_run_results(**payload)
    converted_results = {}
    for k, v in model_run.items():
        converted_results[k] = [
            {"value": t[0], "timestamp": t[1].isoformat()} for t in v
        ]

    return jsonify(converted_results), 200


@blueprint.route("/get-model-run-sensor-measure", methods=["GET"])
@jwt_required()
def get_model_run_sensor_measure() -> Tuple[Response, int]:
    """
    Get the sensor and sensor measure that the output of a model run should
    be compared to.

    GET request should have json data (mimetype "application/json") containing
    {
        run_id: <Database ID of the model run>,
    }

    Returns 200 with
    {
        "sensor_unique_id": <sensor unique id:str>,
        "sensor_measure": {
            "name": <sensor measure name:str>,
            "units": <sensor measure units:str>
        }
    }
    """
    payload = request.get_json()
    required_keys = ["run_id"]
    error_response = check_keys(payload, required_keys, "/get-model-run-sensor-measure")
    if error_response:
        return error_response
    try:
        result = models.get_model_run_sensor_measure(**payload)
        # The sensor_id is not needed in the API return value
        del result["sensor_id"]
    except RowMissingError:
        return jsonify({"message": "No such model run"}), 400
    return jsonify(result), 200
