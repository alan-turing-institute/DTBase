"""
A module for the main dashboard actions
"""
import logging
import copy
import datetime as dt
import numpy as np
import pandas as pd
import json
import pytz

from flask import render_template, request
from flask_login import login_required

from app.home import blueprint


@blueprint.route("/index")
@login_required
def index():
    """
    Index page
    """
    return render_template("index.html")
