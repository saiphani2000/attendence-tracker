from collections import defaultdict

from app.constants import ATTENDANCE_WEIGHTS
from app.extensions import db
from app.models import Attendance, ClassSession, Enrollment, Student


def calculate_attendance_percentage(student_id: int, course_id: int) -> tuple[float, int]:
    """Return (percentage, total_sessions) for a student in a course."""
    sessions = ClassSession.query.filter_by(course_id=course_id).order_by(
        ClassSession.session_date
    ).all()
    total_sessions = len(sessions)
    if total_sessions == 0:
        return 0.0, 0

    session_ids = [s.id for s in sessions]
    records = {
        a.session_id: a.status
        for a in Attendance.query.filter(
            Attendance.student_id == student_id,
            Attendance.session_id.in_(session_ids),
        ).all()
    }

    total_weight = sum(
        ATTENDANCE_WEIGHTS.get(records.get(sid), ATTENDANCE_WEIGHTS['Absent'])
        for sid in session_ids
    )
    return round((total_weight / total_sessions) * 100, 1), total_sessions


def build_course_attendance_reports(course_id: int) -> list[dict]:
    """Build attendance reports for all enrolled students in one pass."""
    sessions = ClassSession.query.filter_by(course_id=course_id).order_by(
        ClassSession.session_date
    ).all()
    session_ids = [s.id for s in sessions]
    total_sessions = len(sessions)

    enrollments = (
        db.session.query(Student)
        .join(Enrollment, Enrollment.student_id == Student.id)
        .filter(Enrollment.course_id == course_id)
        .all()
    )
    student_ids = [s.id for s in enrollments]

    attendance_map = defaultdict(dict)
    if session_ids and student_ids:
        for record in Attendance.query.filter(
            Attendance.session_id.in_(session_ids),
            Attendance.student_id.in_(student_ids),
        ).all():
            attendance_map[record.student_id][record.session_id] = record.status

    reports = []
    for student in enrollments:
        if total_sessions == 0:
            percentage = 0.0
        else:
            total_weight = sum(
                ATTENDANCE_WEIGHTS.get(
                    attendance_map[student.id].get(sid),
                    ATTENDANCE_WEIGHTS['Absent'],
                )
                for sid in session_ids
            )
            percentage = round((total_weight / total_sessions) * 100, 1)

        reports.append({
            'student': student,
            'percentage': percentage,
            'total_sessions': total_sessions,
        })

    reports.sort(key=lambda x: x['percentage'], reverse=True)
    return reports


def get_student_course_data(student_id: int) -> list[dict]:
    """Dashboard data for a student across all enrolled courses."""
    enrollments = Enrollment.query.filter_by(student_id=student_id).all()
    courses_data = []

    for enrollment in enrollments:
        course = enrollment.course
        percentage, total_sessions = calculate_attendance_percentage(student_id, course.id)

        recent_attendance = (
            db.session.query(Attendance, ClassSession)
            .join(ClassSession, Attendance.session_id == ClassSession.id)
            .filter(
                Attendance.student_id == student_id,
                ClassSession.course_id == course.id,
            )
            .order_by(ClassSession.session_date.desc())
            .limit(5)
            .all()
        )

        from app.models import Grade
        grades = Grade.query.filter_by(
            course_id=course.id,
            student_id=student_id,
        ).order_by(Grade.created_at.desc()).all()

        courses_data.append({
            'course': course,
            'percentage': percentage,
            'total_sessions': total_sessions,
            'recent_attendance': recent_attendance,
            'grades': grades,
        })

    return courses_data


def get_attendance_chart_data(course_id: int) -> dict:
    """Aggregate attendance counts per session for Chart.js."""
    sessions = ClassSession.query.filter_by(course_id=course_id).order_by(
        ClassSession.session_date
    ).all()
    labels = [s.session_date.strftime('%Y-%m-%d') for s in sessions]
    counts = {status: [] for status in ATTENDANCE_WEIGHTS}

    for sess in sessions:
        records = Attendance.query.filter_by(session_id=sess.id).all()
        status_counts = {status: 0 for status in ATTENDANCE_WEIGHTS}
        for record in records:
            status_counts[record.status] = status_counts.get(record.status, 0) + 1
        for status in ATTENDANCE_WEIGHTS:
            counts[status].append(status_counts.get(status, 0))

    return {'labels': labels, 'datasets': counts}
