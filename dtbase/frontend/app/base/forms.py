from flask_wtf import FlaskForm
from wtforms.fields import EmailField, PasswordField, SelectField, StringField, URLField


class LoginForm(FlaskForm):
    email = EmailField("Email", id="email_login")
    password = PasswordField("Password", id="pwd_login")


class NewUserForm(FlaskForm):
    email = EmailField("Email", id="email_login")
    password = PasswordField("Password", id="pwd_login")


class NewServiceForm(FlaskForm):
    name = StringField("Name", id="name")
    url = URLField("URL", id="url")
    http_method = SelectField(
        "HTTP method", choices=["POST", "GET", "PUT", "DELETE"], id="http_method"
    )
