"""
Python module to import data from the Rothamsted Research North Wyke Farm Platform API.
"""
from __future__ import annotations

import datetime as dt
import logging
from typing import Optional, cast

import requests

from dtbase.ingress.ingress_base import BaseIngress

ROTHAMSTED_API_BASE_URL = "https://nwfp.rothamsted.ac.uk:8443"

# We are only including these measurements for now, to keep the amount of data and the
# number of queries manageable.
INCLUDED_MEASUREMENTS = {
    "Nitrite and Nitrate",
    "pH",
    "Precipitation",
    "Soil Temperature @ 15cm Depth",
    "Soil Moisture @ 10cm Depth",
    "Soil Moisture @ 20cm Depth",
    "Soil Moisture @ 30cm Depth",
    "Air Temperature",
    "Relative Humidity",
    "Carbon Dioxide",
    "Solar Radiation",
}

# Special values that the catchmentName field may have, but that aren't returned when
# querying for all catchments.
EXTRA_CATCHMENTS = [{"DisplayName": "Met"}]


def query_rothamsted_api(
    method: str, endpoint_name: str, payload: Optional[dict | list] = None
) -> dict | list:
    request_method = getattr(requests, method)
    response = request_method(
        f"{ROTHAMSTED_API_BASE_URL}/{endpoint_name}", json=payload
    )
    if response.status_code != 200:
        raise RuntimeError(f"Failed request to Rothamsted endpoint {endpoint_name}")
    return response.json()


class RothamstedIngress(BaseIngress):
    """
    Class for ingressing data from the Rothamsted API.
    """

    def __init__(self) -> None:
        super().__init__()

    def get_data(
        self, from_dt: dt.datetime, to_dt: dt.datetime
    ) -> list[tuple[str, dict | list]]:
        catchments = cast(list, query_rothamsted_api("get", "getCatchments"))
        catchments += EXTRA_CATCHMENTS
        measurement_types = query_rothamsted_api("get", "getMeasurementTypes")
        return_value: list[tuple[str, dict | list]] = []
        for mt in measurement_types:
            sensor_type_created = False
            measurement_type_name = mt["DisplayName"]
            if measurement_type_name not in INCLUDED_MEASUREMENTS:
                continue
            sensor_type_name = f"{measurement_type_name} Sensor"
            for catchment in catchments:
                catchment_name = catchment["DisplayName"]
                readings = query_rothamsted_api(
                    "post",
                    "getMeasurementsByCatchmentName",
                    {
                        "startDate": from_dt.isoformat(),
                        "endDate": to_dt.isoformat(),
                        "catchmentName": catchment_name,
                        "typeId": mt["Id"],
                    },
                )
                readings = [r for r in readings if r["dataQuality"] == "Acceptable"]
                if not readings:
                    continue

                if not sensor_type_created:
                    # Only create the sensor type if we actually found data for it, and
                    # it hasn't been created before.
                    payload = {
                        "name": sensor_type_name,
                        "description": None,
                        "measures": [
                            {
                                "name": measurement_type_name,
                                "units": mt["Unit"],
                                "datatype": "float",
                            },
                        ],
                    }
                    logging.info(f"Inserting sensor type {payload}")
                    return_value.append(("/sensor/insert-sensor-type", payload))
                    sensor_type_created = True

                sensor_id = f"{catchment_name} {sensor_type_name}"
                payload = {
                    "type_name": sensor_type_name,
                    "unique_identifier": sensor_id,
                }
                logging.info(f"Inserting sensor {payload}")
                return_value.append(("/sensor/insert-sensor", payload))
                timestamps, values = zip(
                    *[(r["DateTime"], float(r["Value"])) for r in readings]
                )
                payload = {
                    "measure_name": measurement_type_name,
                    "unique_identifier": sensor_id,
                    "readings": values,
                    "timestamps": timestamps,
                }
                return_value.append(("/sensor/insert-sensor-readings", payload))
        return return_value


def gather_all_catchment_measurement_pairs() -> dict:
    measurement_types = query_rothamsted_api("get", "getMeasurementTypes")
    return_value = {}
    for mt in measurement_types:
        mt_id = mt["Id"]
        readings = query_rothamsted_api(
            "post",
            "getMeasurementsByTypeId",
            payload={"numPerPage": 500, "page": 1, "typeId": mt_id},
        )
        if not readings:
            continue
        location_names, catch_display_names, data_qualities = (
            set(s)
            for s in zip(
                *[
                    (r["LocationName"], r["CatchDisplayName"], r["dataQuality"])
                    for r in readings
                ]
            )
        )
        return_value[mt_id] = {
            "location_names": location_names,
            "catch_display_names": catch_display_names,
            "data_qualities": data_qualities,
        }
    return return_value


def example_rothamsted_ingress() -> None:
    dt_from = dt.datetime(2022, 1, 1)
    dt_to = dt.datetime(2022, 7, 1)
    ingress = RothamstedIngress()
    ingress.ingress_data(dt_from, dt_to)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    example_rothamsted_ingress()
