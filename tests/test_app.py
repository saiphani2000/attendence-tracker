from datetime import date

from app import seed_demo_data
from app.extensions import db
from app.models import Attendance, ClassSession, Enrollment, User
from app.services.attendance_service import calculate_attendance_percentage


def test_health_endpoint(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.get_json()['status'] == 'healthy'


def test_login_page(client):
    response = client.get('/login')
    assert response.status_code == 200


def test_register_and_login(client):
    response = client.post('/register', data={
        'name': 'New Teacher',
        'email': 'new@test.com',
        'password': 'password123',
        'confirm_password': 'password123',
        'role': 'teacher',
    }, follow_redirects=True)
    assert response.status_code == 200

    response = client.post('/login', data={
        'email': 'new@test.com',
        'password': 'password123',
    }, follow_redirects=True)
    assert response.status_code == 200


def test_attendance_calculation(app, sample_course, sample_student):
    with app.app_context():
        db.session.add(Enrollment(course_id=sample_course, student_id=sample_student))
        session1 = ClassSession(course_id=sample_course, session_date=date(2025, 1, 1))
        session2 = ClassSession(course_id=sample_course, session_date=date(2025, 1, 2))
        db.session.add_all([session1, session2])
        db.session.flush()

        db.session.add(
            Attendance(session_id=session1.id, student_id=sample_student, status='Present'),
        )
        db.session.add(
            Attendance(session_id=session2.id, student_id=sample_student, status='Absent'),
        )
        db.session.commit()

        percentage, total = calculate_attendance_percentage(sample_student, sample_course)
        assert total == 2
        assert percentage == 50.0


def test_seed_demo_data(app):
    with app.app_context():
        seed_demo_data()
        assert User.query.filter_by(email='demo@teacher.com').first() is not None
