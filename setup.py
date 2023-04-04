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
    package_data={"dtbase": ["models/arima/config_arima.ini"]},
#    packages=[
#        "dtbase",
#        "dtbase.core",
#        "dtbase.backend",
#        "dtbase.webapp",
#        "dtbase.functions",
#        "dtbase.ingress",
#        "dtbase.models",
 #   ],
    install_requires=required,
)
