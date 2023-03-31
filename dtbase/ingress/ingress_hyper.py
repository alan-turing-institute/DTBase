"""
Python module to import data using the Hyper.ag API
"""
import os
import json
import logging
import requests


HYPER_URL = "https://zcf.hyper.systems/api/sites/1/analytics/v3/device_metrics"
BACKEND_URL = os.environ["DT_BACKEND_URL"]

# Mapping of Hyper metrics to sensor measures in the database.
METRICS_TO_MEASURES = {
    "aranet_ambient_temperature": {
        "name": "ambient temperature",
        "units": "degrees Celsius",
    },
    "aranet_relative_humidity": {
        "name": "ambient relative humidity",
        "units": "percent",
    },
    "aranet_co2": {
        "name": "ambient CO2",
        "units": "ppm",
    },
    "aranet_current": {
        "name": "aranet air velocity current",
        "units": "amperes",
    },
    "aranet_current_derived": {
        "name": "air velocity",
        "units": "m/s",
    },
    "aegis_ii_temperature": {
        "name": "irrigation water temperature",
        "units": "degrees Celsius",
    },
    "aegis_ii_ph": {
        "name": "irrigation water pH",
        "units": "",
    },
    "aegis_ii_conductivity": {
        "name": "irrigation water conductivity",
        "units": "microsiemens",
    },
    "aegis_ii_disolved_oxygen": {
        "name": "irrigation water dissolved oxygen",
        "units": "percent",
    },
    "aegis_ii_turbidity_ntu": {"name": "irrigation water turbidity", "units": "???"},
    "aegis_ii_peroxide": {
        "name": "irrigation water peroxide content",
        "units": "ppm",
    },
}

# Sensor types that Hyper reports data for
SENSOR_TYPES = [
    {
        "name": "Aranet T&RH",
        "description": "Aranet ambient temperature and relative humidity sensor",
        "measures": [
            {
                "name": "ambient temperature",
                "units": "degrees Celsius",
                "datatype": "float",
            },
            {
                "name": "ambient relative humidity",
                "units": "percent",
                "datatype": "float",
            },
        ],
    },
    {
        "name": "Aranet CO2",
        "description": "Aranet ambient CO2 sensor",
        "measures": [
            {
                "name": "ambient CO2",
                "units": "ppm",
                "datatype": "float",
            }
        ],
    },
    {
        "name": "Aranet air velocity",
        "description": "Aranet air velocity sensor",
        "measures": [
            {
                "name": "aranet air velocity current",
                "units": "amperes",
                "datatype": "float",
            },
            {
                "name": "air velocity",
                "units": "m/s",
                "datatype": "float",
            },
        ],
    },
    {
        "name": "Aegis II",
        "description": "Aegis II irrigation water sensor",
        "measures": [
            {
                "name": "irrigation water turbidity",
                "units": "???",
                "datatype": "float",
            },
            {
                "name": "irrigation water temperature",
                "units": "degrees Celsius",
                "datatype": "float",
            },
            {
                "name": "irrigation water pH",
                "units": "",
                "datatype": "float",
            },
            {
                "name": "irrigation water peroxide content",
                "units": "ppm",
                "datatype": "float",
            },
            {
                "name": "irrigation water dissolved oxygen",
                "units": "percent",
                "datatype": "float",
            },
            {
                "name": "irrigation water conductivity",
                "units": "microsiemens",
                "datatype": "float",
            },
        ],
    },
]


# Mapping of sensor IDs to their types (the Hyper API does not return this information).
SENSORS = {
    "1053355": {"type": "Aranet T&RH"},
    "1058446": {"type": "Aranet T&RH"},
    "1052914": {"type": "Aranet T&RH"},
    "1051155": {"type": "Aranet T&RH"},
    "1061649": {"type": "Aranet T&RH"},
    "1061452": {"type": "Aranet T&RH"},
    "1051907": {"type": "Aranet T&RH"},
    "1053410": {"type": "Aranet T&RH"},
    "1058458": {"type": "Aranet T&RH"},
    "1058485": {"type": "Aranet T&RH"},
    "1061469": {"type": "Aranet T&RH"},
    "1061654": {"type": "Aranet T&RH"},
    "1052066": {"type": "Aranet T&RH"},
    "1058459": {"type": "Aranet T&RH"},
    "3146778": {"type": "Aranet T&RH"},
    "1053333": {"type": "Aranet T&RH"},
    "1061680": {"type": "Aranet T&RH"},
    "1051109": {"type": "Aranet T&RH"},
    "1053541": {"type": "Aranet T&RH"},
    "1058340": {"type": "Aranet T&RH"},
    "1052915": {"type": "Aranet T&RH"},
    "5246038": {"type": "Aranet air velocity"},
    "3146082": {"type": "Aranet CO2"},
    "3146071": {"type": "Aranet CO2"},
    "5244328": {"type": "Aranet air velocity"},
    "5244354": {"type": "Aranet air velocity"},
    "80:1F:12:9C:C5:29": {"type": "Aegis II"},
}


def backend_call(request_type, end_point_path, payload):
    request_func = getattr(requests, request_type)
    url = f"{BACKEND_URL}{end_point_path}"
    headers = {"content-type": "application/json"}
    response = request_func(url, headers=headers, json=json.dumps(payload))
    return response


def log_rest_response(response):
    msg = f"Got response {response.status_code}: {response.text}"
    if 300 > response.status_code:
        logging.info(msg)
    else:
        logging.warning(msg)


def add_sensor_types():
    for sensor_type in SENSOR_TYPES:
        logging.info(f"Inserting sensor type {sensor_type['name']}")
        response = backend_call("post", "/sensor/insert_sensor_type", sensor_type)
        log_rest_response(response)


def add_sensors(metadata):
    add_sensor_types()
    for sensor_id, sensor_info in SENSORS.items():
        sensor_type = sensor_info["type"]
        try:
            name = metadata["devices"][sensor_id]["name"]
        except KeyError:
            logging.info(f"No metadata for sensor {sensor_id}")
            continue
        logging.info(f"Inserting sensor {sensor_id}, {name}")
        payload = {
            "unique_identifier": sensor_id,
            "name": name,
        }
        response = backend_call("post", f"/sensor/insert_sensor/{sensor_type}", payload)
        log_rest_response(response)


def query_hyper_api(api_key, dt_from, dt_to, metrics):
    """
    Makes a request to download sensor data for specified metrics for a specified period
    of time.  Note that this gets data for _all_ sensors, and returns it as a dict,
    keyed by Aranet id.

    Arguments:
        api_key: api key for authentication
        dt_from: date range from
        dt_to: date range to
        columns: list of dictionaries containing metric names, as defined in
        READINGS_DICTS
    Return:
        success: whether data request was succesful
        error: error message
        data_df_dict: dictionary of {aranet_pro_id (str): DataFrame of sensor_data}
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + api_key,
    }
    dt_from_iso = dt_from.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    dt_to_iso = dt_to.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    url = HYPER_URL
    # get metrics as a single string, comma-separating each metric name
    metrics = ",".join(metrics)
    params = {
        "start_time": dt_from_iso,
        "end_time": dt_to_iso,
        "metrics": metrics,
        "resolution": "10m",
        "metadata": "true",
    }
    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        error = "Request's [%s] status code: %d" % (url[:70], response.status_code)
        return False, error, {}
    data = response.json()
    error = ""
    success = True
    return success, error, data


def import_hyper_data(api_key, dt_from, dt_to, create_sensors=False):
    """
    This is the main function for this module.
    Uploads data to the DTBase database, for various metrics, from the Hyper.ag API.

    Arguments:
        api_key: Hyper API key
        dt_from: date range from
        dt_to: date range to
        create_sensors: Create new sensors in the database if they don't exist. False by
            default.
    Returns:
        success, error
    """
    metrics = METRICS_TO_MEASURES.keys()
    logging.info(f"Calling Hyper API from {dt_from} to {dt_to}.")
    success, error, data = query_hyper_api(api_key, dt_from, dt_to, metrics)
    if not success:
        logging.error(error)
        return success, error
    metadata = data["metadata"]
    all_timestamps = data["labels"]
    series = data["series"]
    logging.info("Got data from Hyper for sensors.")

    if create_sensors:
        add_sensors(metadata)

    for s in series:
        metric = s["metric"]
        device_id = s["device_id"]
        device_name = metadata["devices"][device_id]["name"]
        values = s["values"]
        # Some values may be None, filter those out.
        timestamps, values = zip(
            *((t, v) for t, v in zip(all_timestamps, values) if v is not None)
        )
        logging.info(f"Uploading data for sensor {device_id}, {device_name}.")
        payload = {
            "measure_name": METRICS_TO_MEASURES[metric]["name"],
            "sensor_uniq_id": device_id,
            "readings": values,
            "timestamps": timestamps,
        }
        response = backend_call("post", "/sensor/insert_sensor_readings", payload)
        log_rest_response(response)
    logging.info("Done uploading data.")
    error = ""
    success = True
    return success, error
