from dtbase.core.utils import *
from dtbase.models.arima.run_pipeline import *
session = get_db_session()
run_pipeline(session)

