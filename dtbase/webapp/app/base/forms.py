from flask_wtf import FlaskForm
from wtforms.fields import EmailField, PasswordField


class LoginForm(FlaskForm):
    email = EmailField("Email", id="email_login")
    password = PasswordField("Password", id="pwd_login")


class NewUserForm(FlaskForm):
    email = EmailField("Email", id="email_login")
    password = PasswordField("Password", id="pwd_login")
