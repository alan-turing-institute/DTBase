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
        measurement_types = cast(
            list, query_rothamsted_api("get", "getMeasurementTypes")
        )
        measurement_types_by_id = {mt["Id"]: mt for mt in measurement_types}
        catchment_measurement_types = cast(
            list, query_rothamsted_api("get", "getCatchmentMeasurementTypes")
        )

        sensor_types_created = set()
        sensors_created = set()
        return_value: list[tuple[str, dict | list]] = []
        for cmt in catchment_measurement_types:
            mt = measurement_types_by_id[cmt["type_id"]]
            catchment_name = cmt["catchment_name"]
            if catchment_name is None and cmt["location_Name"] == "Met":
                # "Met" is considered a catchment by some API endpoints, and not by
                # others, so this gets a bit confusing.
                catchment_name = "Met"

            readings = query_rothamsted_api(
                "post",
                "getMeasurementsByCatchmentName",
                {
                    "startDate": from_dt.isoformat(),
                    "endDate": to_dt.isoformat(),
                    "catchmentName": catchment_name,
                    "typeId": cmt["type_id"],
                },
            )
            readings = [r for r in readings if r["dataQuality"] == "Acceptable"]
            if not readings:
                continue

            # Only create the sensor type if we actually found data for it, and it
            # hasn't been created before.
            sensor_type_name = f"{mt['DisplayName']} Sensor"
            if sensor_type_name not in sensor_types_created:
                payload = {
                    "name": sensor_type_name,
                    "description": None,
                    "measures": [
                        {
                            "name": mt["DisplayName"],
                            "units": mt["Unit"],
                            "datatype": "float",
                        },
                    ],
                }
                logging.info(f"Inserting sensor type {payload}")
                return_value.append(("/sensor/insert-sensor-type", payload))
                sensor_types_created.add(sensor_type_name)

            # Only create the sensor if we actually found data for it, and it hasn't
            # been created before.
            sensor_id = f"{catchment_name} {sensor_type_name}"
            if sensor_id not in sensors_created:
                payload = {
                    "type_name": sensor_type_name,
                    "unique_identifier": sensor_id,
                }
                logging.info(f"Inserting sensor {payload}")
                return_value.append(("/sensor/insert-sensor", payload))
                sensors_created.add(sensor_id)

            timestamps, values = zip(
                *[(r["DateTime"], float(r["Value"])) for r in readings]
            )
            payload = {
                "measure_name": mt["DisplayName"],
                "unique_identifier": sensor_id,
                "readings": values,
                "timestamps": timestamps,
            }
            return_value.append(("/sensor/insert-sensor-readings", payload))
        return return_value


def example_rothamsted_ingress() -> None:
    dt_from = dt.datetime(2022, 1, 1)
    dt_to = dt.datetime(2022, 7, 1)
    ingress = RothamstedIngress()
    ingress.ingress_data(dt_from, dt_to)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    example_rothamsted_ingress()
