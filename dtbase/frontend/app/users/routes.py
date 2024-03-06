"""Routes for the users section of the site."""
from flask import flash, render_template, request
from flask_login import current_user, login_required

from dtbase.frontend.app.base.forms import NewUserForm
from dtbase.frontend.app.users import blueprint


@blueprint.route("/index", methods=["GET", "POST"])
@login_required
def index() -> str:
    """The index page of users."""
    new_user_form = NewUserForm(request.form)
    if request.method == "POST":
        if "submitDelete" in request.form:
            payload = {"email": request.form["email"]}
            response = current_user.backend_call(
                "post", "/user/delete-user", payload=payload
            )
            if response.status_code == 200:
                flash("User deleted successfully", "success")
            else:
                flash("Failed to delete user", "error")
        else:
            new_user_form.validate_on_submit()
            payload = {
                "email": request.form["email"],
                "password": request.form["password"],
            }
            response = current_user.backend_call(
                "post", "/user/create-user", payload=payload
            )
            if response.status_code == 201:
                flash("User created successfully", "success")
            else:
                flash("Failed to create user", "error")
    users = current_user.backend_call("get", "/user/list-users").json()
    return render_template("users.html", new_user_form=new_user_form, users=users)
