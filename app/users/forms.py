# app/users/forms.py

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, TextAreaField, SelectField, DateField
from wtforms.validators import DataRequired, Length, Email, Optional


class EditProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=120)])
    last_name = StringField('Last Name', validators=[Length(max=120)])
    phone = StringField('Phone', validators=[Length(max=30)])

    # Profile Specifics
    date_of_birth = DateField('Date of Birth', format='%Y-%m-%d', validators=[Optional()])
    gender = SelectField('Gender',
                         choices=[('', 'Select...'), ('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')],
                         validators=[Optional()])
    address = TextAreaField('Address', validators=[Length(max=500)])

    # Avatar
    avatar = FileField('Update Profile Picture', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])

    submit = SubmitField('Update Profile')