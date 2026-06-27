import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    DEFAULT_SECRET_KEY = 'dev-secret-key-change-in-production'

    @staticmethod
    def init_app(app):
        if app.config.get('TESTING'):
            return

        database_url = os.environ.get('DATABASE_URL', 'sqlite:///instance/student_tracker.db')
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url

        is_production = os.environ.get('FLASK_ENV') == 'production'
        app.config['SESSION_COOKIE_SECURE'] = is_production

        if is_production and app.config['SECRET_KEY'] == Config.DEFAULT_SECRET_KEY:
            raise RuntimeError('SECRET_KEY must be set in production')


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'


config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}
