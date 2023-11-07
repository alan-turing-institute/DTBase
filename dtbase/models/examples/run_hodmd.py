import os
from datetime import datetime

from dtbase.core.utils import get_db_session
from dtbase.models.hodmd.run_pipeline import run_pipeline

plots_save_path = "./plots/hodmd/" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
if not os.path.exists(plots_save_path):
    os.makedirs(plots_save_path)

session = get_db_session()
# run_pipeline(session, plots_save_path, multi_measure=False)
run_pipeline(session, plots_save_path, multi_measure=True)
