"""
Module (routes.py) to handle API endpoints related to authentication
"""
import flask_jwt_extended as fjwt
from flask import jsonify, request

from dtbase.backend.api.auth import blueprint
from dtbase.backend.utils import check_keys
from dtbase.core import users
from dtbase.core.structure import SQLA as db


@blueprint.route("/login", methods=["POST"])
def new_token():
    """
    Generate a new authentication token.

    POST request should have json data (mimetype "application/json")
    containing
    {
      "email": <type_email:str>,
      "password": <type_password:str>
    }

    Returns 401 if credentials are invalid, or otherwise 200 with the payload
    {
        "access_token: <type_access_token:str>,
        "refresh_token: <type_access_token:str>
    }
    """

    payload = request.get_json()
    required_keys = ["email", "password"]
    error_response = check_keys(payload, required_keys, "/login")
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
    refresh_token = fjwt.create_refresh_token(identity=email)
    return jsonify({"access_token": access_token, "refresh_token": refresh_token}), 200


@blueprint.route("/refresh", methods=["POST"])
@fjwt.jwt_required(refresh=True)
def refresh():
    """
    Refresh an authentication token.

    No payload is required for this request.

    It returns output similar to new_token, only the authentication method is different
    (checking the validity of a refresh token rather than email and password.
    """
    identity = fjwt.get_jwt_identity()
    access_token = fjwt.create_access_token(identity=identity)
    refresh_token = fjwt.create_refresh_token(identity=identity)
    return jsonify({"access_token": access_token, "refresh_token": refresh_token}), 200
