"""
Importing Hyper.ag data using Azure FunctionApp.
"""

import os
from datetime import datetime, timedelta, timezone
import logging

from ingress_hyper import import_hyper_data


def hyper_import():
    """
    The main Hyper import Azure Function routine.
    """
    logging.basicConfig(level=logging.INFO)

    utc_timestamp = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
    logging.info("Python Hyper timer trigger function started at %s", utc_timestamp)

    dt_to = datetime.utcnow()
    dt_from = dt_to - timedelta(days=180)
    api_key = os.environ["DT_HYPER_API_KEY"]
    import_hyper_data(api_key, dt_from, dt_to, create_sensors=True)

    utc_timestamp = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
    logging.info("Python Hyper timer trigger function finished at %s", utc_timestamp)


hyper_import()
