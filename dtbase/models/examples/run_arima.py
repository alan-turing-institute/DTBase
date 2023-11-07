from dtbase.core.utils import get_db_session
from dtbase.models.arima.run_pipeline import run_pipeline

session = get_db_session()
run_pipeline(session)
