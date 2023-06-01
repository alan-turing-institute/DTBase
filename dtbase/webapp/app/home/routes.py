"""
A module for the main dashboard actions
"""
import datetime as dt
import json
import re

from flask import render_template, request
from flask_login import login_required
import pandas as pd

from dtbase.webapp.app.home import blueprint
from dtbase.webapp import utils


@blueprint.route("/index")
@login_required
def index():
    """Index page."""

    return render_template(
        "index.html",
    )
