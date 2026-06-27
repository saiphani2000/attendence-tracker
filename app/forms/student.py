from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional


class StudentEnrollForm(FlaskForm):
    full_name = StringField('Student Name', validators=[DataRequired(), Length(max=200)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    student_id = StringField('Student ID', validators=[Optional(), Length(max=50)])
    password = PasswordField(
        'Initial Password',
        validators=[DataRequired(), Length(min=8)],
        description='Student will use this to log in',
    )
    course_id = SelectField('Course', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Enroll Student')
