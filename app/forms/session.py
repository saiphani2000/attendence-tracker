from flask_wtf import FlaskForm
from wtforms import DateField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class SessionForm(FlaskForm):
    course_id = SelectField('Course', coerce=int, validators=[DataRequired()])
    session_date = DateField('Session Date', validators=[DataRequired()])
    topic = StringField('Topic', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Save Session')
