# app/auth/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Regexp


class LoginForm(FlaskForm):
    class Meta:
        csrf = False
    email = StringField(
        "Email:  ",
        validators=[
            DataRequired(),
            Email(),
            Length(max=120)
        ]
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=6)
        ]
    )

    submit = SubmitField("Login")


class RegisterForm(FlaskForm):
    class Meta:
        csrf = False

    # Replace username with these two fields
    first_name = StringField("First Name", validators=[DataRequired(), Length(max=120)])
    last_name = StringField("Last Name", validators=[Length(max=120)])

    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    phone = StringField("Phone", validators=[Length(max=15)])
    submit = SubmitField("Create Account")
