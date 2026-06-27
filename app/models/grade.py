from app.extensions import db
from app.models.user import utcnow


class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False, index=True)
    assignment_name = db.Column(db.String(200), nullable=False)
    grade_value = db.Column(db.Float, nullable=False)
    max_points = db.Column(db.Float, default=100.0)
    assignment_type = db.Column(db.String(50), nullable=True)
    due_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    course = db.relationship('Course', backref='grades')
    student = db.relationship('Student', backref='grades')

    __table_args__ = (
        db.UniqueConstraint(
            'course_id', 'student_id', 'assignment_name',
            name='unique_grade_assignment',
        ),
    )
