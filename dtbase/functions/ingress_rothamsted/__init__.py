from __future__ import annotations

import datetime as dt
import logging
from typing import Optional

from azure.functions import HttpRequest, HttpResponse
from pydantic import BaseModel, Field, ValidationError

from dtbase.ingress.ingress_rothamsted import RothamstedIngress


class FunctionParameters(BaseModel):
    from_dt: dt.datetime = Field(..., description="Start date of data to ingress.")
    to_dt: dt.datetime = Field(..., description="End date of data to ingress.")
    measurement_type_names: Optional[list[str]] = Field(
        None, description="List of measurement type names to ingress."
    )
    catchment_names: Optional[list[str]] = Field(
        None, description="List of catchment names to ingress."
    )


def main(req: HttpRequest) -> HttpResponse:
    logging.info("Starting Rothamsted ingress function.")

    try:
        req_body = req.get_json()
    except ValueError:
        return HttpResponse("Request body must be valid JSON.", status_code=400)
    # Make pydantic validate the parameters.
    try:
        params = FunctionParameters(**req_body).dict()
    except ValidationError as e:
        return HttpResponse(f"Invalid parameters: {e}", status_code=400)

    ingress = RothamstedIngress()
    ingress.ingress_data(**params)

    logging.info("Finished Rothamsted ingress.")
    return HttpResponse("Successfully ingressed data.", status_code=200)
