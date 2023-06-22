import os

from setuptools import setup, find_packages

with open("requirements.txt") as f:
    required = f.read().splitlines()

setup(
    name="dtbase",
    version="0.1",
    description="core functionality for a generic digital twin",
    url="https://github.com/alan-turing-institute/DTBase",
    author="The Alan Turing Institute Research Engineering Group",
    license="MIT",
    packages=find_packages(),
    package_data={"dtbase": ["models/arima/arima/config_arima.ini", "models/utils/dataprocessor/data_config.ini"]},
    entry_points={
        "console_scripts": ["dtbase_start_postgres_docker=dtbase.core.db_docker:main"]
    },
    install_requires=required,
)
