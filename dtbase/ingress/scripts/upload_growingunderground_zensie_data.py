#!/usr/bin/env python

"""
Upload some curated Zensie temperature and relative humidity data
provided in a csv file.
"""
import os
import requests
import pandas as pd

# BASE_URL = "https://dtbasetest-backend0736b858.azurewebsites.net"
BASE_URL = "http://localhost:5000"

TUNNEL_AISLES_DICT = {
    "Tunnel3": ["A", "B"],
    "Tunnel4": ["E"],
    "Tunnel5": ["C"],
    "Tunnel6": ["D"],
}

AISLES_COLUMNS_DICT = {"A": 32, "B": 32, "C": 24, "D": 16, "E": 12}
NUM_SHELVES = 4

SENSORS = {
    18: {"name": "Farm_T/RH_16B1", "unique_identifier": "009E5"},
    27: {"name": "Farm_T/RH_16B2", "unique_identifier": "00DA2"},
    23: {"name": "Farm_T/RH_16B4", "unique_identifier": "01295"},
}

FILENAME = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "data",
    "ZensieTRH_18-23-27_2021-22.csv",
)


def add_gu_location_schema():
    """
    Add the location schema used in the Growing Underground farm in Clapham
    """
    payload = {
        "name": "growingunderground",
        "description": "As used in Clapham",
        "identifiers": [
            {"name": "zone", "units": "", "datatype": "string"},
            {"name": "aisle", "units": "", "datatype": "string"},
            {"name": "column", "units": "", "datatype": "integer"},
            {"name": "shelf", "units": "", "datatype": "integer"},
        ],
    }
    r = requests.post(BASE_URL + "/location/insert_location_schema", json=payload)
    if r.status_code != 201:
        raise RuntimeError(f"Error uploading location schema {r.content}")


def add_gu_locations():
    """
    Add all possible locations in the Growing Underground farm.
    """
    for zone, aisle_list in TUNNEL_AISLES_DICT.items():
        for aisle in aisle_list:
            for column in range(1, AISLES_COLUMNS_DICT[aisle] + 1):
                for shelf in range(1, NUM_SHELVES + 1):
                    payload = {
                        "zone": zone,
                        "aisle": aisle,
                        "column": column,
                        "shelf": shelf,
                    }
                    r = requests.post(
                        BASE_URL + "/location/insert_location/growingunderground",
                        json=payload,
                    )
                    if r.status_code != 201:
                        raise RuntimeError(f"Error uploading location {r.content}")
                    pass
                pass
            pass
        pass
    return


def add_sensor_type():
    """
    Add the Zensie T/RH sensor type to the DB
    """
    payload = {
        "name": "zensie-trh",
        "description": "temperature and relative humidity",
        "measures": [
            {"name": "temperature", "units": "degrees C", "datatype": "float"},
            {"name": "humidity", "units": "percent", "datatype": "float"},
        ],
    }
    r = requests.post(BASE_URL + "/sensor/insert_sensor_type", json=payload)
    if r.status_code != 201:
        raise RuntimeError(f"Error uploading sensor type {r.content}")
    return


def add_sensors():
    """
    Add the specific sensors to the database.
    """

    for payload in SENSORS.values():
        r = requests.post(BASE_URL + "/sensor/insert_sensor/zensie-trh", json=payload)
        if r.status_code != 201:
            raise RuntimeError(f"Error uploading sensor {r.content}")
    return


def add_sensor_locations():
    """
    Add sensor locations to the db for the sensors added in add_sensors
    """
    pass


def add_sensor_data(filename):
    df = pd.read_csv(filename)
    for sensor_id in SENSORS.keys():
        for measure in ["temperature", "humidity"]:
            print(f"Uploading sensor data for {measure} sensor {sensor_id}")
            colname = f"{measure}_{sensor_id}"
            df_notnull = df[df[colname].notnull()]
            payload = {
                "measure_name": measure,
                "sensor_uniq_id": SENSORS[sensor_id]["unique_identifier"],
                "readings": list(df_notnull[colname]),
                "timestamps": list(df_notnull["timestamp"]),
            }
            r = requests.post(BASE_URL + "/sensor/insert_sensor_readings", json=payload)
            if r.status_code != 201:
                raise RuntimeError(f"Error uploading sensor data{r.content}")


if __name__ == "__main__":
    print("Uploading location schema ...")
    add_gu_location_schema()
    print("Uploading locations ...")
    add_gu_locations()
    print("Uploading sensor types ...")
    add_sensor_type()
    print("Uploading sensors ...")
    add_sensors()
    print("Uploading sensor data ...")
    add_sensor_data(FILENAME)
