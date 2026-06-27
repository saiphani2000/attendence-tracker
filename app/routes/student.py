from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.services.attendance_service import get_student_course_data
from app.utils.decorators import student_required

bp = Blueprint('student', __name__, url_prefix='/student')


@bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    profile = current_user.student_profile
    if not profile:
        flash('Student profile not found. Contact your teacher.', 'error')
        return redirect(url_for('main.index'))

    courses_data = get_student_course_data(profile.id)
    return render_template('student_dashboard.html', student=profile, courses_data=courses_data)
