from __future__ import annotations

import logging

from azure.functions import HttpRequest, HttpResponse

from dtbase.models.arima import ArimaModel


def main(req: HttpRequest) -> HttpResponse:
    logging.info("Starting Arima function.")

    try:
        config = req.get_json()
    except ValueError:
        if req.get_body():
            return HttpResponse("Malformed body, JSON expected", status_code=400)
        config = None

    arima = ArimaModel(config)
    arima()

    logging.info("Finished Arima function.")
    return HttpResponse("Successfully ran Arima.", status_code=200)
