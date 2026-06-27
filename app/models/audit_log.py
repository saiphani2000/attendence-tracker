from app.extensions import db
from app.models.user import utcnow


class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False)
    entity_type = db.Column(db.String(50), nullable=True)
    entity_id = db.Column(db.Integer, nullable=True)
    timestamp = db.Column(db.DateTime, default=utcnow, index=True)
    ip_address = db.Column(db.String(45), nullable=True)

    user = db.relationship('User', backref='audit_logs')
