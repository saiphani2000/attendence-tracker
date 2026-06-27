import pytest

from app import create_app
from app.extensions import db
from app.models import Course, Student, User


@pytest.fixture
def app():
    application = create_app('testing')
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def teacher(app):
    with app.app_context():
        user = User(name='Test Teacher', email='teacher@test.com', role='teacher')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        return user.id


@pytest.fixture
def sample_course(app, teacher):
    with app.app_context():
        course = Course(name='Math 101', teacher_id=teacher)
        db.session.add(course)
        db.session.commit()
        return course.id


@pytest.fixture
def sample_student(app):
    with app.app_context():
        user = User(name='Jane Doe', email='jane@test.com', role='student')
        user.set_password('password123')
        db.session.add(user)
        db.session.flush()
        student = Student(user_id=user.id, full_name='Jane Doe', email='jane@test.com')
        db.session.add(student)
        db.session.commit()
        return student.id
