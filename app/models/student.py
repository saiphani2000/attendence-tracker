from app.extensions import db
from app.models.user import utcnow


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False, index=True,
    )
    full_name = db.Column(db.String(200), nullable=False)
    student_id = db.Column(db.String(50), unique=True, nullable=True)
    email = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    user = db.relationship('User', back_populates='student_profile')

    def __repr__(self):
        return f'<Student {self.full_name}>'
