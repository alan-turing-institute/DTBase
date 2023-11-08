"""
Module (routes.py) to handle API endpoints related to authentication
"""
import flask_jwt_extended as fjwt
from flask import jsonify, request

from dtbase.backend.api.auth import blueprint
from dtbase.backend.utils import check_keys
from dtbase.core import users
from dtbase.core.structure import SQLA as db


@blueprint.route("/new-token", methods=["POST"])
def new_token():
    """
    Generate a new authentication token.
    POST request should have json data (mimetype "application/json")
    containing
    {
      "email": <type_email:str>,
      "password": <type_password:str>
    }
    """

    payload = request.get_json()
    required_keys = ["email", "password"]
    error_response = check_keys(payload, required_keys, "/new-token")
    if error_response:
        return error_response
    email = payload["email"]
    password = payload["password"]

    session = db.session
    session.begin()
    valid_login = users.check_password(email, password, session=session)
    session.commit()
    if not valid_login:
        return jsonify({"error": "Invalid email or password"}), 401

    access_token = fjwt.create_access_token(identity=email)
    return jsonify(access_token=access_token), 200
