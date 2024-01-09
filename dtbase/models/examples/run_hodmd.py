import os
from datetime import datetime

from dtbase.models.hodmd.run_pipeline import run_pipeline

plots_save_path = "./plots/hodmd/" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
if not os.path.exists(plots_save_path):
    os.makedirs(plots_save_path)

# run_pipeline(plots_save_path, multi_measure=False)
run_pipeline(plots_save_path, multi_measure=True)
