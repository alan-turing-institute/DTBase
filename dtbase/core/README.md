# DTBase Core

This folder holds all code that is used by more than one part of the DTBase package. The main parts of DTBase, such as frontend, backend, and services, should never import anything from one another. If they share any code, that code should be in core.

Currently the only things here are:
* `exc.py` for some custom exception types we raise.
* `utils.py` for miscellaneous utils, mostly for making calling the backend API endpoints smoother.
* `constants.py` which reads in a large number of environment variables that are considered package-level constants. These include things like the URL for the backend and the password of the default user.
