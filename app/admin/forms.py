# app/admin/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Optional, Length

class ApplicationEditForm(FlaskForm):
    name = StringField("Full name", validators=[DataRequired(), Length(max=200)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=180)])
    phone = StringField("Phone", validators=[Optional(), Length(max=50)])
    program = SelectField("Program", validators=[Optional()], choices=[])
    message = TextAreaField("Message", validators=[Optional(), Length(max=2000)])
    status = SelectField("Status", choices=[("new", "New"), ("reviewed", "Reviewed"), ("accepted", "Accepted"), ("rejected", "Rejected")], default="new")
    admin_note = TextAreaField("Admin note", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Save")
