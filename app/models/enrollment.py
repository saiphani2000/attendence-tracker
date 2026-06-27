from app.extensions import db
from app.models.user import utcnow


class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False, index=True)
    enrolled_at = db.Column(db.DateTime, default=utcnow)

    course = db.relationship('Course', backref='enrollments')
    student = db.relationship('Student', backref='enrollments')

    __table_args__ = (
        db.UniqueConstraint('course_id', 'student_id', name='unique_enrollment'),
    )
