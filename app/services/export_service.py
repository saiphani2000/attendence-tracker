import csv
import io
from datetime import datetime

from app.extensions import db
from app.models import Attendance, ClassSession, Course, Enrollment, Student


def export_students_csv(course_id: int) -> tuple[io.BytesIO, str]:
    course = Course.query.get_or_404(course_id)
    enrollments = (
        db.session.query(Enrollment, Student)
        .join(Student, Enrollment.student_id == Student.id)
        .filter(Enrollment.course_id == course_id)
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Student ID', 'Full Name', 'Email', 'Enrolled Date'])

    for enrollment, student in enrollments:
        writer.writerow([
            student.student_id or '',
            student.full_name,
            student.email or '',
            enrollment.enrolled_at.strftime('%Y-%m-%d') if enrollment.enrolled_at else '',
        ])

    filename = f"{course.name.replace(' ', '_')}_students_{datetime.now().strftime('%Y%m%d')}.csv"
    return io.BytesIO(output.getvalue().encode('utf-8')), filename


def export_attendance_csv(course_id: int) -> tuple[io.BytesIO, str]:
    course = Course.query.get_or_404(course_id)
    sessions = ClassSession.query.filter_by(course_id=course_id).order_by(
        ClassSession.session_date
    ).all()
    enrollments = (
        db.session.query(Enrollment, Student)
        .join(Student, Enrollment.student_id == Student.id)
        .filter(Enrollment.course_id == course_id)
        .all()
    )

    session_ids = [s.id for s in sessions]
    attendance_lookup = {}
    if session_ids:
        for record in Attendance.query.filter(Attendance.session_id.in_(session_ids)).all():
            attendance_lookup[(record.student_id, record.session_id)] = record.status

    output = io.StringIO()
    writer = csv.writer(output)
    header = ['Student ID', 'Full Name'] + [
        s.session_date.strftime('%Y-%m-%d') for s in sessions
    ]
    writer.writerow(header)

    for _, student in enrollments:
        row = [student.student_id or '', student.full_name]
        for sess in sessions:
            row.append(attendance_lookup.get((student.id, sess.id), 'Absent'))
        writer.writerow(row)

    filename = f"{course.name.replace(' ', '_')}_attendance_{datetime.now().strftime('%Y%m%d')}.csv"
    return io.BytesIO(output.getvalue().encode('utf-8')), filename
