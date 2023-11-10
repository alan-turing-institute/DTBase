from flask_wtf import FlaskForm
from wtforms import PasswordField, TextField

## login and registration


class LoginForm(FlaskForm):
    email = TextField("Email", id="email_login")
    password = PasswordField("Password", id="pwd_login")


class CreateAccountForm(FlaskForm):
    email = TextField("Email", id="email_create")
    password = PasswordField("Password", id="pwd_create")
