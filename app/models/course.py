from app.extensions import db
from app.models.user import utcnow


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=True)
    term = db.Column(db.String(50), nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    is_active = db.Column(db.Boolean, default=True)

    teacher = db.relationship('User', backref='courses')
