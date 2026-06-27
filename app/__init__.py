import logging
import os

from dotenv import load_dotenv
from flask import Flask

load_dotenv()

logging.basicConfig(
    level=getattr(logging, os.environ.get('LOG_LEVEL', 'INFO').upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
        if config_name == 'production':
            config_name = 'production'
        elif os.environ.get('TESTING'):
            config_name = 'testing'
        else:
            config_name = 'default'

    from app.config import config_by_name

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    os.makedirs(os.path.join(base_dir, 'instance'), exist_ok=True)
    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, 'templates'),
        static_folder=os.path.join(base_dir, 'static'),
    )
    app.config.from_object(config_by_name[config_name])
    config_by_name[config_name].init_app(app)

    if not app.config.get('TESTING'):
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if db_uri.startswith('sqlite:///') and not db_uri.startswith('sqlite:////'):
            db_file = db_uri.replace('sqlite:///', '')
            if not os.path.isabs(db_file):
                db_uri = f'sqlite:///{os.path.join(base_dir, db_file)}'
                app.config['SQLALCHEMY_DATABASE_URI'] = db_uri

    from app.extensions import csrf, db, limiter, login_manager, migrate
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    limiter.enabled = not app.config.get('TESTING', False)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.routes.admin import bp as admin_bp
    from app.routes.auth import bp as auth_bp
    from app.routes.main import bp as main_bp
    from app.routes.student import bp as student_bp
    from app.routes.teacher import bp as teacher_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)

    return app


def seed_demo_data():
    """Create demo accounts if database is empty."""
    from app.extensions import db
    from app.models import Student, User

    if User.query.first():
        return

    teacher = User(name='Demo Teacher', email='demo@teacher.com', role='teacher')
    teacher.set_password('demo12345')
    db.session.add(teacher)

    admin = User(name='Admin', email='admin@school.com', role='admin')
    admin.set_password('admin12345')
    db.session.add(admin)

    student_user = User(name='John Doe', email='john@student.com', role='student')
    student_user.set_password('student123')
    db.session.add(student_user)
    db.session.flush()

    db.session.add(Student(
        user_id=student_user.id,
        full_name='John Doe',
        student_id='S001',
        email='john@student.com',
    ))
    db.session.commit()
