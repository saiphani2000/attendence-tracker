import logging

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db, limiter
from app.forms.auth import LoginForm, RegisterForm
from app.models import User, utcnow
from app.services.audit_service import log_action

logger = logging.getLogger(__name__)

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit('10 per minute')
def login():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password.', 'error')
            return render_template('login.html', form=form)

        if not user.is_active:
            flash('Account is disabled.', 'error')
            return render_template('login.html', form=form)

        login_user(user, remember=True)
        user.last_login = utcnow()
        log_action(user.id, 'auth.login')
        db.session.commit()
        flash(f'Welcome back, {user.name}!', 'success')
        return _redirect_by_role(user)

    return render_template('login.html', form=form)


@bp.route('/register', methods=['GET', 'POST'])
@limiter.limit('5 per minute')
def register():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            name=form.name.data.strip(),
            email=form.email.data.lower().strip(),
            role=form.role.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()

        if user.role == 'student':
            from app.models import Student
            db.session.add(Student(
                user_id=user.id,
                full_name=user.name,
                email=user.email,
            ))

        log_action(user.id, 'auth.register')
        db.session.commit()
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html', form=form)


@bp.route('/logout')
@login_required
def logout():
    log_action(current_user.id, 'auth.logout')
    db.session.commit()
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('main.index'))


def _redirect_by_role(user):
    if user.is_teacher:
        return redirect(url_for('teacher.dashboard'))
    if user.is_student:
        return redirect(url_for('student.dashboard'))
    if user.is_admin:
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('main.index'))
