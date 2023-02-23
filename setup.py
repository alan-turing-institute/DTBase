import os
from setuptools import setup

with open("requirements.txt") as f:
    required = f.read().splitlines()

setup(
    name="dtbase",
    version="0.1",
    description="core functionality for a generic digital twin",
    url="https://github.com/alan-turing-institute/DTBase",
    author="The Alan Turing Institute Research Engineering Group",
    license="MIT",
    packages=["dtbase"],
    install_requires=required,
    zip_safe=False,
)
