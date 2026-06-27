import logging

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_wtf.csrf import CSRFError

from app.extensions import db

logger = logging.getLogger(__name__)

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    return render_template('index.html')


@bp.route('/health')
def health():
    try:
        db.session.execute(db.text('SELECT 1'))
        return {'status': 'healthy', 'database': 'connected'}, 200
    except Exception as exc:
        logger.error('Health check failed: %s', exc)
        return {'status': 'unhealthy', 'database': 'disconnected'}, 503


@bp.app_errorhandler(404)
def not_found(error):
    flash('Page not found.', 'error')
    return redirect(url_for('main.index'))


@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    logger.error('Internal server error: %s', error)
    flash('An internal error occurred.', 'error')
    return redirect(url_for('main.index'))


@bp.app_errorhandler(CSRFError)
def handle_csrf(error):
    flash('Session expired. Please try again.', 'error')
    return redirect(url_for('main.index'))
