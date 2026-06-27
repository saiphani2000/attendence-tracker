from flask import request

from app.extensions import db
from app.models import AuditLog


def log_action(user_id, action, entity_type=None, entity_id=None):
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=request.remote_addr if request else None,
    )
    db.session.add(entry)
