from app.extensions import db
from app.models.user import utcnow


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(
        db.Integer, db.ForeignKey('class_session.id'), nullable=False, index=True,
    )
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    session = db.relationship('ClassSession', backref='attendance_records')
    student = db.relationship('Student', backref='attendance_records')

    __table_args__ = (
        db.UniqueConstraint('session_id', 'student_id', name='unique_attendance'),
    )
