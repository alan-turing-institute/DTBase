"""
Module (routes.py) to handle API endpoints related to sensors
"""
from datetime import datetime, timedelta
import json
import sqlalchemy as sqla
from flask import request, jsonify
from flask_login import login_required

from dtbase.backend.api.sensor import blueprint
from dtbase.core import sensors, sensor_locations
from dtbase.core.structure import SQLA as db
from dtbase.core.utils import jsonify_query_result
from dtbase.backend.utils import check_keys


@blueprint.route("/insert-sensor-type", methods=["POST"])
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

    payload = request.get_json()
    required_keys = ["name", "description", "measures"]
    error_response = check_keys(payload, required_keys, "/insert_sensor_type")
    if error_response:
        return error_response

    db.session.begin()
    for measure in payload["measures"]:
        try:
            sensors.insert_sensor_measure(
                name=measure["name"],
                units=measure["units"],
                datatype=measure["datatype"],
                session=db.session,
            )
        except sqla.exc.IntegrityError:
            db.session.rollback()
    try:
        sensors.insert_sensor_type(
            name=payload["name"],
            description=payload["description"],
            measures=payload["measures"],
            session=db.session,
        )
    except sqla.exc.IntegrityError:
        db.session.rollback()

    db.session.commit()
    return jsonify(payload), 201


@blueprint.route("/insert-sensor", methods=["POST"])
# @login_required
def insert_sensor():
    """
    Add a sensor to the database.

    POST request should have json data (mimetype "application/json") containing
    {
      "type_name": <sensor_type_name:str>,
      "unique_identifier": <unique identifier:str>,
    }
    by which the sensor will be distinguished from all others, and optionally
    {
      "name": <human readable name:str>,
      "notes": <human readable notes:str>
    }
    """

    payload = request.get_json()
    required_keys = {"unique_identifier", "type_name"}
    error_response = check_keys(payload, required_keys, "/insert_sensor")
    if error_response:
        return error_response
    try:
        sensors.insert_sensor(**payload, session=db.session)
    except sqla.exc.IntegrityError:
        db.session.rollback()
    db.session.commit()
    return jsonify(payload), 201


@blueprint.route("/insert-sensor-location", methods=["POST"])
# @login_required
def insert_sensor_location():
    """
    Add a sensor location installation to the database.

    POST request should have json data (mimetype "application/json") containing
    {
      "unique_identifier": <unique identifier of the sensor:str>,
      "location_schema": <name of the location schema to use:str>,
      "coordinates": <coordinates to the location:dict>
    }
    where the coordinates dict is keyed by location identifiers.
    and optionally also
    {
      "installation_datetime": <date from which the sensor has been at this location:str>
    }
    If no installation date is given, it's assumed to be now.
    """
    payload = request.get_json()
    required_keys = {"unique_identifier", "schema_name", "coordinates"}
    error_response = check_keys(payload, required_keys, "/insert-sensor-location")
    if error_response:
        return error_response
    if "installation_datetime" not in payload:
        payload["installation_datetime"] = datetime.now()
    sensor_locations.insert_sensor_location(
        sensor_uniq_id=payload["unique_identifier"],
        schema_name=payload["schema_name"],
        coordinates=payload["coordinates"],
        installation_datetime=payload["installation_datetime"],
        session=db.session,
    )
    db.session.commit()
    return jsonify(payload), 201


@blueprint.route("/list-sensor-locations", methods=["GET"])
# @login_required
def list_sensor_locations():
    """
    Get the location history of a sensor.

    GET request should have json data (mimetype "application/json") containing
    {
      "unique_identifier": <unique identifier of the sensor:str>,
    }
    """

    payload = request.get_json()
    required_keys = {"unique_identifier"}
    error_response = check_keys(payload, required_keys, "/list-sensor-locations")
    if error_response:
        return error_response
    result = sensor_locations.get_location_history(
        sensor_uniq_id=payload["unique_identifier"], session=db.session
    )
    return jsonify(result), 200


@blueprint.route("/insert-sensor-readings", methods=["POST"])
# @login_required
def insert_sensor_readings():
    """
    Add sensor readings to the database.

    POST request should have JSON data (mimetype "application/json") containing
    {
      "measure_name": <measure_name:str>,
      "unique_identifier": <sensor_unique_identifier:str>,
      "readings": <list of readings>,
      "timestamps": <list of timestamps in ISO 8601 format '%Y-%m-%dT%H:%M:%S'>
    }
    """

    payload = request.get_json()
    required_keys = ["measure_name", "unique_identifier", "readings", "timestamps"]
    error_response = check_keys(payload, required_keys, "/insert-sensor-readings")
    if error_response:
        return error_response

    measure_name = payload["measure_name"]
    sensor_uniq_id = payload["unique_identifier"]
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


@blueprint.route("/list-sensors", methods=["GET"])
# @login_required
def list_sensors():
    """
    List sensors of a particular type in the database.
    Optionally takes a payload of the form
    {"type_name": <sensor_type_name:str>}

        Will return results in the form:
    [
        {
        "id": <id:int>,
        "name": <name:str>,
        "notes": <notes:str>,
        "sensor_type_id": <sensor_type_id:int>,
        "type_name": <sensor_type_name:str>,
        "unique_identifier": <unique_identifier:str>
        },
        ...
    ]
    """
    payload = request.get_json()
    if "type_name" in payload.keys():
        result = sensors.list_sensors(
            type_name=payload.get("type_name"), session=db.session
        )
    else:
        sensors.list_sensors(session=db.session)
    return jsonify(result), 200


@blueprint.route("/list-sensor-types", methods=["GET"])
# @login_required
def list_sensor_types():
    """
    List sensor types in the database.
    Returns results in the form:
    [
        {
        "description": <description:str>,
        "id": <id:int>,
        "measures": [
            {"datatype": <datatype:str>, "name": <name:str>, "units": <units:str>},
            ...
            ],
        "name": "sensor_name"
        },
        ...
    ]
    """
    result = sensors.list_sensor_types(session=db.session)
    return jsonify(result), 200


@blueprint.route("/list-measures", methods=["GET"])
# @login_required
def list_sensor_measures():
    """
    List sensor measures in the database.
    Returns results in the form:
    [
    {"datatype": <datatype:str>, "id": <id:int>, "name": <name:str>, "units": <units:str>},
    ...
    ]
    """
    result = sensors.list_sensor_measures(session=db.session)
    return jsonify(result), 200


@blueprint.route("/sensor-readings", methods=["GET"])
# @login_required
def get_sensor_readings():
    """
    Get sensor readings for a specific measure and sensor between two dates.

    GET request should have JSON data (mimetype "application/json") containing:
        measure_name: Name of the sensor measure to get readings for.
        unique_identifier: Unique identifier for the sensor to get readings for.
        dt_from: Datetime string for earliest readings to get. Inclusive. In ISO 8601 format: '%Y-%m-%dT%H:%M:%S'.
        dt_to: Datetime string for last readings to get. Inclusive. In ISO 8601 format: '%Y-%m-%dT%H:%M:%S'.
    """

    payload = request.get_json()

    required_keys = ["measure_name", "unique_identifier", "dt_from", "dt_to"]
    error_response = check_keys(payload, required_keys, "/get-sensor-readings")
    if error_response:
        return error_response

    measure_name = payload.get("measure_name")
    sensor_uniq_id = payload.get("unique_identifier")
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
        {"value": reading[0], "timestamp": reading[1].isoformat()}
        for reading in readings
    ]

    return jsonify(readings_json), 200


@blueprint.route("/delete-sensor", methods=["DELETE"])
# @login_required
def delete_sensor():
    """
    Delete a sensor from the database.

    Expects a payload of the form
    {"unique_identifier": <sensor_unique_id:str>}
    """
    payload = request.get_json()
    required_keys = ["unique_identifier"]
    error_response = check_keys(payload, required_keys, "/delete-sensor")
    unique_identifier = payload.get("unique_identifier")
    if error_response:
        return error_response
    sensors.delete_sensor(unique_identifier=unique_identifier, session=db.session)
    db.session.commit()
    return jsonify({"message": "Sensor deleted"}), 200


@blueprint.route("/delete-sensor-type", methods=["DELETE"])
# @login_required
def delete_sensor_type():
    """
    Delete a sensor type from the database.

    Expects a payload of the form
    {"type_name": <sensor_type_name:str>}
    """
    payload = request.get_json()
    required_keys = ["type_name"]
    error_response = check_keys(payload, required_keys, "/delete-sensor-type")
    type_name = payload.get("type_name")
    if error_response:
        return error_response
    sensors.delete_sensor_type(type_name=type_name, session=db.session)
    db.session.commit()
    return jsonify({"message": "Sensor type deleted"}), 200
