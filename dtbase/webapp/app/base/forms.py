from flask_wtf import FlaskForm
from wtforms import PasswordField
from wtforms.fields.html5 import EmailField


class LoginForm(FlaskForm):
    email = EmailField("Email", id="email_login")
    password = PasswordField("Password", id="pwd_login")


class NewUserForm(FlaskForm):
    email = EmailField("Email", id="email_login")
    password = PasswordField("Password", id="pwd_login")
