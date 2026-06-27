from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please login to access this page', 'error')
                return redirect(url_for('auth.login'))
            if current_user.role not in roles:
                flash('Access denied.', 'error')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


teacher_required = role_required('teacher')
student_required = role_required('student')
admin_required = role_required('admin')
