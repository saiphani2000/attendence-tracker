from flask_wtf import FlaskForm
from wtforms import DateField, FloatField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class GradeForm(FlaskForm):
    student_id = SelectField('Student', coerce=int, validators=[DataRequired()])
    assignment_name = StringField('Assignment Name', validators=[DataRequired(), Length(max=200)])
    grade_value = FloatField('Grade', validators=[DataRequired(), NumberRange(min=0)])
    max_points = FloatField(
        'Max Points', validators=[Optional(), NumberRange(min=0.01)], default=100.0,
    )
    assignment_type = SelectField(
        'Type',
        choices=[
            ('', 'Select type...'),
            ('exam', 'Exam'),
            ('quiz', 'Quiz'),
            ('homework', 'Homework'),
            ('project', 'Project'),
            ('participation', 'Participation'),
            ('other', 'Other'),
        ],
        validators=[Optional()],
    )
    due_date = DateField('Due Date', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save Grade')
