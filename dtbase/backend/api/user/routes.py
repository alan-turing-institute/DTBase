"""
Module (routes.py) to handle API endpoints related to user management
"""
from typing import Tuple

from flask import Response, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError, NoResultFound

from dtbase.backend.api.user import blueprint
from dtbase.backend.utils import check_keys
from dtbase.core import users
from dtbase.core.structure import db


@blueprint.route("/list-users", methods=["GET"])
@jwt_required()
def list_users() -> Tuple[Response, int]:
    """
    List all users.

    A GET request with no payload needed.

    Returns 200.
    """
    emails = users.list_users()
    return jsonify(emails), 200


@blueprint.route("/create-user", methods=["POST"])
@jwt_required()
def create_user() -> Tuple[Response, int]:
    """
    Create a new user.

    POST request should have json data (mimetype "application/json") containing
    {
      "email": <type_email:str>,
      "password": <type_password:str>
    }

    Returns 409 if user already exists, otherwise 201.
    """
    payload = request.get_json()
    required_keys = ["email", "password"]
    error_response = check_keys(payload, required_keys, "/create-user")
    if error_response:
        return error_response
    email = payload.get("email")
    password = payload.get("password")
    try:
        users.insert_user(email, password, session=db.session)
    except IntegrityError:
        return jsonify({"message": "User already exists"}), 409
    db.session.commit()
    return jsonify({"message": "User created"}), 201


@blueprint.route("/delete-user", methods=["DELETE"])
@jwt_required()
def delete_user() -> Tuple[Response, int]:
    """
    Delete a user.

    POST request should have json data (mimetype "application/json") containing
    {
      "email": <type_email:str>,
    }

    Returns 200.
    """
    payload = request.get_json()
    required_keys = ["email"]
    error_response = check_keys(payload, required_keys, "/delete-user")
    if error_response:
        return error_response
    email = payload.get("email")
    try:
        users.delete_user(email, session=db.session)
    except ValueError:
        return jsonify({"message": "User doesn't exist"}), 400
    db.session.commit()
    return jsonify({"message": "User deleted"}), 200


@blueprint.route("/change-password", methods=["POST"])
@jwt_required()
def change_password() -> Tuple[Response, int]:
    """
    Change a user's password.

    POST request should have JSON data (mimetype "application/json") containing
    {
      "email": <type_email:str>,
      "current_password": <type_current_password:str>,
      "new_password": <type_new_password:str>,
      "confirm_new_password": <type_confirm_new_password:str>,
    }
    where `new_password` is the new password and `confirm_new_password`
      must match `new_password`.

    Returns 400 if user doesn't exist, if current password is incorrect,
      or if passwords do not match. Otherwise, returns 200.
    """
    payload = request.get_json()
    required_keys = [
        "email",
        "current_password",
        "new_password",
        "confirm_new_password",
    ]
    error_response = check_keys(payload, required_keys, "/change-password")
    if error_response:
        return error_response

    email = payload.get("email")
    current_password = payload.get("current_password")
    new_password = payload.get("new_password")
    confirm_new_password = payload.get("confirm_new_password")

    if new_password != confirm_new_password:
        return (
            jsonify({"message": "New password and confirm new password do not match"}),
            400,
        )

    try:
        # Assuming `verify_password` checks the current password is correct
        if not users.verify_password(email, current_password, session=db.session):
            return jsonify({"message": "Current password is incorrect"}), 400

        users.change_password(email, new_password, session=db.session)
    except NoResultFound:
        return jsonify({"message": "User doesn't exist"}), 400

    db.session.commit()
    return jsonify({"message": "Password changed successfully"}), 200
