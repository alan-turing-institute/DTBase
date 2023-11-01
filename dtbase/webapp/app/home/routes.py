"""
A module for the main dashboard actions
"""

from flask import render_template
from flask_login import login_required

from dtbase.webapp.app.home import blueprint


@blueprint.route("/index")
@login_required
def index():
    """Index page."""

    return render_template(
        "index.html",
    )
