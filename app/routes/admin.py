from flask import Blueprint, render_template
from flask_login import login_required

from app.models import AuditLog, ClassSession, Course, Student, User
from app.utils.decorators import admin_required

bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    stats = {
        'users': User.query.count(),
        'teachers': User.query.filter_by(role='teacher').count(),
        'students': Student.query.count(),
        'courses': Course.query.filter_by(is_active=True).count(),
        'sessions': ClassSession.query.count(),
    }
    recent_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(20).all()
    return render_template('admin_dashboard.html', stats=stats, recent_logs=recent_logs)
