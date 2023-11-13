from typing import Any, Union

from flask import (
    abort,
    current_app,
    # jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import login_required, login_user, logout_user
from werkzeug.wrappers import Response

from dtbase.webapp.app import login_manager
from dtbase.webapp.app.base import blueprint
from dtbase.webapp.app.base.forms import LoginForm
from dtbase.webapp.exc import AuthorizationError
from dtbase.webapp.user import User
from dtbase.webapp.utils import url_has_allowed_host_and_scheme


@blueprint.route("/")
def route_default() -> Response:
    return redirect(url_for("base_blueprint.login"))


@blueprint.route("/<template>")
@login_required
def route_template(template: str) -> Response:
    return render_template(template + ".html")


@blueprint.route("/fixed_<template>")
@login_required
def route_fixed_template(template: str) -> Response:
    return render_template("fixed/fixed_{}.html".format(template))


@blueprint.route("/page_<error>")
def route_errors(error: Any) -> Response:
    return render_template("errors/page_{}.html".format(error))


@blueprint.route("/backend_not_found_error")
def route_backend_not_found() -> Response:
    return render_template("errors/backend_not_found.html")


@blueprint.route("/favicon.ico")
def favicon() -> Response:
    return current_app.send_static_file("favicon.ico")


## Login & Registration


@blueprint.route("/login", methods=["GET", "POST"])
def login() -> Union[Response, str]:
    login_form = LoginForm(request.form)
    # The validate only passes if this is a POST request.
    if login_form.validate_on_submit():
        user = User(request.form["email"])
        try:
            user.authenticate(request.form["password"])
        except AuthorizationError:
            return render_template("errors/page_401.html")
        login_user(user)

        next = request.args.get("next")
        # url_has_allowed_host_and_scheme checks if the url is safe for redirects,
        # meaning it matches the request host.
        if next and not url_has_allowed_host_and_scheme(next, request.host):
            abort(400)
        return redirect(next or url_for("home_blueprint.index"))
    return render_template("login/login.html", login_form=login_form)


# @blueprint.route("/create_user", methods=["POST"])
# @login_required
# def create_user():
#     success, result = utils.create_user(**request.form)
#     return jsonify({"success": success, "output": result})


@blueprint.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("base_blueprint.login"))


# Errors


@login_manager.unauthorized_handler
def unauthorized_callback() -> Response:
    return redirect(url_for("base_blueprint.login"))


@blueprint.errorhandler(403)
def access_forbidden(error: Any) -> Response:
    return redirect(url_for("base_blueprint.login"))


@blueprint.errorhandler(404)
def not_found_error(error: Any) -> Response:
    return render_template("errors/page_404.html"), 404


@blueprint.errorhandler(500)
def internal_error(error: Any) -> Response:
    return render_template("errors/page_500.html"), 500
