"""
Module (routes.py) to handle API endpoints related to sensors
"""
from datetime import datetime, timedelta
import json

from flask import request, jsonify
from flask_login import login_required

from dtbase.backend.api.sensor import blueprint
from dtbase.core import sensors, sensor_locations
from dtbase.core.structure import SQLA as db
from dtbase.core.utils import jsonify_query_result
from dtbase.backend.utils import check_keys


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
    required_keys = ["name", "description", "measures"]
    error_response = check_keys(payload, required_keys, "/insert_sensor_type")
    if error_response:
        return error_response

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
    required_keys = {"unique_identifier"}
    error_response = check_keys(payload, required_keys, "/insert_sensor")
    if error_response:
        return error_response
    sensors.insert_sensor(type_name=type_name, **payload, session=db.session)
    db.session.commit()
    return jsonify(payload), 201


@blueprint.route("/insert_sensor_location", methods=["POST"])
# @login_required
def insert_sensor_location():
    """
    Add a sensor location installation to the database.

    POST request should have json data (mimetype "application/json") containing
    {
      "sensor_identifier": <unique identifier of the sensor:str>,
      "location_schema": <name of the location schema to use:str>,
      "coordinates": <coordinates to the location:str>
    }
    and optionally also
    {
      "installation_datetime": <date from which the sensor has been at this location:str>
    }
    If no installation date is given, it's assumed to be now.
    """

    payload = json.loads(request.get_json())
    required_keys = {"sensor_identifier", "location_schema", "coordinates"}
    error_response = check_keys(payload, required_keys, "/insert_sensor_location")
    if error_response:
        return error_response
    if "installation_datetime" not in payload:
        payload["installation_datetime"] = datetime.now()
    sensor_locations.insert_sensor_location(
        sensor_uniq_id=payload["sensor_identifier"],
        schema_name=payload["location_schema"],
        coordinates=payload["coordinates"],
        installation_datetime=payload["installation_datetime"],
        session=db.session,
    )
    db.session.commit()
    return jsonify(payload), 201


@blueprint.route("/list_sensor_locations", methods=["GET"])
# @login_required
def list_sensor_locations():
    """
    Get the location history of a sensor.

    GET request should have json data (mimetype "application/json") containing
    {
      "unique_identifier": <unique identifier of the sensor:str>,
    }
    """

    payload = json.loads(request.get_json())
    required_keys = {"unique_identifier"}
    error_response = check_keys(payload, required_keys, "/list_sensor_location")
    if error_response:
        return error_response
    result = sensor_locations.get_location_history(
        sensor_uniq_id=payload["unique_identifier"], session=db.session
    )
    return jsonify(result), 200


@blueprint.route("/insert_sensor_readings", methods=["POST"])
# @login_required
def insert_sensor_readings():
    """
    Add sensor readings to the database.

    POST request should have JSON data (mimetype "application/json") containing
    {
      "measure_name": <measure_name:str>,
      "sensor_uniq_id": <sensor_unique_identifier:str>,
      "readings": <list of readings>,
      "timestamps": <list of timestamps in ISO 8601 format '%Y-%m-%dT%H:%M:%S'>
    }
    """

    payload = json.loads(request.get_json())
    required_keys = ["measure_name", "sensor_uniq_id", "readings", "timestamps"]
    error_response = check_keys(payload, required_keys, "/insert_sensor_readings")
    if error_response:
        return error_response

    measure_name = payload["measure_name"]
    sensor_uniq_id = payload["sensor_uniq_id"]
    readings = payload["readings"]
    timestamps = payload["timestamps"]

    # Convert timestamps from strings to datetime objects
    try:
        timestamps = [datetime.fromisoformat(ts) for ts in timestamps]
    except ValueError:
        return (
            jsonify({"error": "Invalid datetime format. Use '%Y-%m-%dT%H:%M:%S'"}),
            400,
        )

    db.session.begin()
    try:
        sensors.insert_sensor_readings(
            measure_name=measure_name,
            sensor_uniq_id=sensor_uniq_id,
            readings=readings,
            timestamps=timestamps,
            session=db.session,
        )
    except Exception:
        db.session.rollback()
        raise
    db.session.commit()

    return jsonify(payload), 201


@blueprint.route("/list", methods=["GET"])
# @login_required
def list_sensors():
    """List sensors in the database."""
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


@blueprint.route("/sensor_readings", methods=["GET"])
# @login_required
def get_sensor_readings():
    """
    Get sensor readings for a specific measure and sensor between two dates.

    GET request should have JSON data (mimetype "application/json") containing:
        measure_name: Name of the sensor measure to get readings for.
        sensor_uniq_id: Unique identifier for the sensor to get readings for.
        dt_from: Datetime string for earliest readings to get. Inclusive. In ISO 8601 format: '%Y-%m-%dT%H:%M:%S'.
        dt_to: Datetime string for last readings to get. Inclusive. In ISO 8601 format: '%Y-%m-%dT%H:%M:%S'.
    """

    payload = json.loads(request.get_json())

    required_keys = ["measure_name", "sensor_uniq_id", "dt_from", "dt_to"]
    error_response = check_keys(payload, required_keys, "/get_sensor_readings")
    if error_response:
        return error_response

    measure_name = payload.get("measure_name")
    sensor_uniq_id = payload.get("sensor_uniq_id")
    dt_from = payload.get("dt_from")
    dt_to = payload.get("dt_to")

    # Convert dt_from and dt_to to datetime objects
    try:
        dt_from = datetime.fromisoformat(dt_from)
        dt_to = datetime.fromisoformat(dt_to)
    except ValueError:
        return (
            jsonify(
                {
                    "error": "Invalid datetime format. Use ISO format: '%Y-%m-%dT%H:%M:%S'"
                }
            ),
            400,
        )

    readings = sensors.get_sensor_readings(
        measure_name, sensor_uniq_id, dt_from, dt_to, session=db.session
    )

    # Convert readings to JSON-friendly format
    readings_json = [
        {"value": reading[0], "timestamp": reading[1]} for reading in readings
    ]

    return jsonify(readings_json), 200


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
