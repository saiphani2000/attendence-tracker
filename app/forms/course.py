from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional


class CourseForm(FlaskForm):
    name = StringField('Course Name', validators=[DataRequired(), Length(max=200)])
    code = StringField('Course Code', validators=[Optional(), Length(max=50)])
    description = TextAreaField('Description', validators=[Optional()])
    term = StringField('Term / Semester', validators=[Optional(), Length(max=50)])
    submit = SubmitField('Save Course')
