from app.extensions import db
from app.models.user import utcnow


class ClassSession(db.Model):
    __tablename__ = 'class_session'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False, index=True)
    session_date = db.Column(db.Date, nullable=False)
    topic = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    course = db.relationship('Course', backref='class_sessions')

    __table_args__ = (
        db.UniqueConstraint('course_id', 'session_date', name='unique_class_session'),
    )
