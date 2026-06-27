import csv
import io
import logging

from flask import Blueprint, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.forms.course import CourseForm
from app.forms.grade import GradeForm
from app.forms.session import SessionForm
from app.forms.student import StudentEnrollForm
from app.models import (
    Attendance,
    ClassSession,
    Course,
    Enrollment,
    Grade,
    Student,
    User,
    utcnow,
)
from app.services.attendance_service import (
    build_course_attendance_reports,
    get_attendance_chart_data,
)
from app.services.audit_service import log_action
from app.services.export_service import export_attendance_csv, export_students_csv
from app.utils.decorators import teacher_required

logger = logging.getLogger(__name__)

bp = Blueprint('teacher', __name__, url_prefix='/teacher')


def _get_teacher_course(course_id):
    return Course.query.filter_by(id=course_id, teacher_id=current_user.id, is_active=True).first()


@bp.route('/dashboard')
@login_required
@teacher_required
def dashboard():
    page = request.args.get('page', 1, type=int)
    courses = Course.query.filter_by(teacher_id=current_user.id, is_active=True).order_by(
        Course.created_at.desc()
    ).paginate(page=page, per_page=6, error_out=False)

    recent_sessions = (
        ClassSession.query.join(Course)
        .filter(Course.teacher_id == current_user.id)
        .order_by(ClassSession.session_date.desc())
        .limit(5)
        .all()
    )

    total_students = (
        db.session.query(Student)
        .join(Enrollment)
        .join(Course)
        .filter(Course.teacher_id == current_user.id)
        .distinct()
        .count()
    )

    return render_template(
        'teacher_dashboard.html',
        courses=courses,
        recent_sessions=recent_sessions,
        teacher_name=current_user.name,
        total_students=total_students,
    )


@bp.route('/course/new', methods=['GET', 'POST'])
@login_required
@teacher_required
def create_course():
    form = CourseForm()
    if form.validate_on_submit():
        course = Course(
            name=form.name.data.strip(),
            code=form.code.data.strip() or None,
            description=form.description.data.strip() or None,
            term=form.term.data.strip() or None,
            teacher_id=current_user.id,
        )
        db.session.add(course)
        log_action(current_user.id, 'course.create', 'course', None)
        db.session.commit()
        flash('Course created successfully!', 'success')
        return redirect(url_for('teacher.dashboard'))
    return render_template('course_form.html', form=form, course=None)


@bp.route('/course/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
@teacher_required
def edit_course(course_id):
    course = _get_teacher_course(course_id)
    if not course:
        flash('Course not found.', 'error')
        return redirect(url_for('teacher.dashboard'))

    form = CourseForm(obj=course)
    if form.validate_on_submit():
        course.name = form.name.data.strip()
        course.code = form.code.data.strip() or None
        course.description = form.description.data.strip() or None
        course.term = form.term.data.strip() or None
        log_action(current_user.id, 'course.update', 'course', course.id)
        db.session.commit()
        flash('Course updated.', 'success')
        return redirect(url_for('teacher.dashboard'))
    return render_template('course_form.html', form=form, course=course)


@bp.route('/course/<int:course_id>/delete', methods=['POST'])
@login_required
@teacher_required
def delete_course(course_id):
    course = _get_teacher_course(course_id)
    if not course:
        flash('Course not found.', 'error')
        return redirect(url_for('teacher.dashboard'))
    course.is_active = False
    log_action(current_user.id, 'course.delete', 'course', course.id)
    db.session.commit()
    flash('Course archived.', 'success')
    return redirect(url_for('teacher.dashboard'))


@bp.route('/student/new', methods=['GET', 'POST'])
@login_required
@teacher_required
def create_student():
    courses = Course.query.filter_by(teacher_id=current_user.id, is_active=True).all()
    form = StudentEnrollForm()
    form.course_id.choices = [(c.id, c.name) for c in courses]

    if form.validate_on_submit():
        course = _get_teacher_course(form.course_id.data)
        if not course:
            flash('Invalid course.', 'error')
            return render_template('student_form.html', form=form, courses=courses)

        email = form.email.data.lower().strip()
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            if existing_user.role != 'student' or not existing_user.student_profile:
                flash('Email already used by another account.', 'error')
                return render_template('student_form.html', form=form, courses=courses)
            student = existing_user.student_profile
        else:
            user = User(
                name=form.full_name.data.strip(),
                email=email,
                role='student',
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.flush()
            student = Student(
                user_id=user.id,
                full_name=form.full_name.data.strip(),
                student_id=form.student_id.data.strip() or None,
                email=email,
            )
            db.session.add(student)

        if Enrollment.query.filter_by(course_id=course.id, student_id=student.id).first():
            flash('Student already enrolled in this course.', 'error')
            return render_template('student_form.html', form=form, courses=courses)

        db.session.add(Enrollment(course_id=course.id, student_id=student.id))
        log_action(current_user.id, 'student.enroll', 'student', student.id)
        db.session.commit()
        flash('Student enrolled successfully!', 'success')
        return redirect(url_for('teacher.dashboard'))

    if request.args.get('course_id'):
        try:
            form.course_id.data = int(request.args.get('course_id'))
        except (TypeError, ValueError):
            pass

    return render_template('student_form.html', form=form, courses=courses)


@bp.route('/enrollment/<int:enrollment_id>/remove', methods=['POST'])
@login_required
@teacher_required
def unenroll_student(enrollment_id):
    enrollment = (
        db.session.query(Enrollment)
        .join(Course)
        .filter(Enrollment.id == enrollment_id, Course.teacher_id == current_user.id)
        .first()
    )
    if not enrollment:
        flash('Enrollment not found.', 'error')
        return redirect(url_for('teacher.dashboard'))
    course_id = enrollment.course_id
    db.session.delete(enrollment)
    log_action(current_user.id, 'student.unenroll', 'enrollment', enrollment_id)
    db.session.commit()
    flash('Student unenrolled.', 'success')
    return redirect(url_for('teacher.attendance_report', course_id=course_id))


@bp.route('/session/new', methods=['GET', 'POST'])
@login_required
@teacher_required
def create_session():
    courses = Course.query.filter_by(teacher_id=current_user.id, is_active=True).all()
    form = SessionForm()
    form.course_id.choices = [(c.id, c.name) for c in courses]

    if form.validate_on_submit():
        course = _get_teacher_course(form.course_id.data)
        if not course:
            flash('Invalid course.', 'error')
            return render_template('session_form.html', form=form, courses=courses)

        if ClassSession.query.filter_by(
            course_id=course.id, session_date=form.session_date.data
        ).first():
            flash('Session already exists for this date.', 'error')
            return render_template('session_form.html', form=form, courses=courses)

        session_obj = ClassSession(
            course_id=course.id,
            session_date=form.session_date.data,
            topic=form.topic.data.strip() or None,
        )
        db.session.add(session_obj)
        log_action(current_user.id, 'session.create', 'class_session', None)
        db.session.commit()
        flash('Session created!', 'success')
        return redirect(url_for('teacher.mark_attendance', session_id=session_obj.id))

    return render_template('session_form.html', form=form, courses=courses)


@bp.route('/session/<int:session_id>/edit', methods=['GET', 'POST'])
@login_required
@teacher_required
def edit_session(session_id):
    session_obj = ClassSession.query.get_or_404(session_id)
    if not _get_teacher_course(session_obj.course_id):
        flash('Access denied.', 'error')
        return redirect(url_for('teacher.dashboard'))

    courses = Course.query.filter_by(teacher_id=current_user.id, is_active=True).all()
    form = SessionForm(obj=session_obj)
    form.course_id.choices = [(c.id, c.name) for c in courses]

    if form.validate_on_submit():
        session_obj.course_id = form.course_id.data
        session_obj.session_date = form.session_date.data
        session_obj.topic = form.topic.data.strip() or None
        log_action(current_user.id, 'session.update', 'class_session', session_obj.id)
        db.session.commit()
        flash('Session updated.', 'success')
        return redirect(url_for('teacher.mark_attendance', session_id=session_obj.id))

    return render_template('session_form.html', form=form, courses=courses, session_obj=session_obj)


@bp.route('/session/<int:session_id>/delete', methods=['POST'])
@login_required
@teacher_required
def delete_session(session_id):
    session_obj = ClassSession.query.get_or_404(session_id)
    course = _get_teacher_course(session_obj.course_id)
    if not course:
        flash('Access denied.', 'error')
        return redirect(url_for('teacher.dashboard'))
    course_id = course.id
    db.session.delete(session_obj)
    log_action(current_user.id, 'session.delete', 'class_session', session_id)
    db.session.commit()
    flash('Session deleted.', 'success')
    return redirect(url_for('teacher.attendance_report', course_id=course_id))


@bp.route('/attendance/<int:session_id>', methods=['GET', 'POST'])
@login_required
@teacher_required
def mark_attendance(session_id):
    session_obj = ClassSession.query.get_or_404(session_id)
    course = _get_teacher_course(session_obj.course_id)
    if not course:
        flash('Access denied.', 'error')
        return redirect(url_for('teacher.dashboard'))

    enrollments = (
        db.session.query(Enrollment, Student)
        .join(Student, Enrollment.student_id == Student.id)
        .filter(Enrollment.course_id == session_obj.course_id)
        .all()
    )

    if request.method == 'POST':
        try:
            for _, student in enrollments:
                status = request.form.get(f'status_{student.id}')
                notes = request.form.get(f'notes_{student.id}', '').strip()
                if status:
                    record = Attendance.query.filter_by(
                        session_id=session_id, student_id=student.id
                    ).first()
                    if record:
                        record.status = status
                        record.notes = notes or None
                        record.updated_at = utcnow()
                    else:
                        db.session.add(Attendance(
                            session_id=session_id,
                            student_id=student.id,
                            status=status,
                            notes=notes or None,
                        ))
            log_action(current_user.id, 'attendance.save', 'class_session', session_id)
            db.session.commit()
            flash('Attendance saved!', 'success')
            return redirect(url_for('teacher.mark_attendance', session_id=session_id))
        except Exception as exc:
            db.session.rollback()
            logger.error('Error saving attendance: %s', exc)
            flash('Error saving attendance.', 'error')

    attendance_records = {
        a.student_id: {'status': a.status, 'notes': a.notes}
        for a in Attendance.query.filter_by(session_id=session_id).all()
    }

    return render_template(
        'attendance_form.html',
        session=session_obj,
        course=course,
        enrollments=enrollments,
        attendance_records=attendance_records,
    )


@bp.route('/report/<int:course_id>')
@login_required
@teacher_required
def attendance_report(course_id):
    course = _get_teacher_course(course_id)
    if not course:
        flash('Access denied.', 'error')
        return redirect(url_for('teacher.dashboard'))

    student_reports = build_course_attendance_reports(course_id)
    chart_data = get_attendance_chart_data(course_id)
    total_sessions = student_reports[0]['total_sessions'] if student_reports else 0

    return render_template(
        'attendance_report.html',
        course=course,
        student_reports=student_reports,
        total_sessions=total_sessions,
        chart_data=chart_data,
    )


@bp.route('/export/students/<int:course_id>')
@login_required
@teacher_required
def export_students(course_id):
    if not _get_teacher_course(course_id):
        flash('Access denied.', 'error')
        return redirect(url_for('teacher.dashboard'))
    try:
        data, filename = export_students_csv(course_id)
        return send_file(data, mimetype='text/csv', as_attachment=True, download_name=filename)
    except Exception as exc:
        logger.error('Export error: %s', exc)
        flash('Export failed.', 'error')
        return redirect(url_for('teacher.attendance_report', course_id=course_id))


@bp.route('/export/attendance/<int:course_id>')
@login_required
@teacher_required
def export_attendance(course_id):
    if not _get_teacher_course(course_id):
        flash('Access denied.', 'error')
        return redirect(url_for('teacher.dashboard'))
    try:
        data, filename = export_attendance_csv(course_id)
        return send_file(data, mimetype='text/csv', as_attachment=True, download_name=filename)
    except Exception as exc:
        logger.error('Export error: %s', exc)
        flash('Export failed.', 'error')
        return redirect(url_for('teacher.attendance_report', course_id=course_id))


@bp.route('/import/students/<int:course_id>', methods=['POST'])
@login_required
@teacher_required
def import_students(course_id):
    course = _get_teacher_course(course_id)
    if not course:
        flash('Access denied.', 'error')
        return redirect(url_for('teacher.dashboard'))

    file = request.files.get('file')
    if not file or not file.filename.endswith('.csv'):
        flash('Please upload a valid CSV file.', 'error')
        return redirect(url_for('teacher.attendance_report', course_id=course_id))

    try:
        stream = io.StringIO(file.stream.read().decode('utf-8'), newline=None)
        reader = csv.DictReader(stream)
        imported = skipped = 0

        for row in reader:
            full_name = row.get('Full Name', '').strip()
            email = row.get('Email', '').strip().lower()
            if not full_name or not email:
                skipped += 1
                continue

            student_id_val = row.get('Student ID', '').strip()
            user = User.query.filter_by(email=email).first()
            if user and user.student_profile:
                student = user.student_profile
            elif user:
                skipped += 1
                continue
            else:
                user = User(name=full_name, email=email, role='student')
                user.set_password('ChangeMe123!')
                db.session.add(user)
                db.session.flush()
                student = Student(
                    user_id=user.id,
                    full_name=full_name,
                    student_id=student_id_val or None,
                    email=email,
                )
                db.session.add(student)
                db.session.flush()

            if Enrollment.query.filter_by(course_id=course_id, student_id=student.id).first():
                skipped += 1
                continue

            db.session.add(Enrollment(course_id=course_id, student_id=student.id))
            imported += 1

        log_action(current_user.id, 'student.import', 'course', course_id)
        db.session.commit()
        flash(f'Imported {imported} students. {skipped} skipped.', 'success')
    except Exception as exc:
        db.session.rollback()
        logger.error('Import error: %s', exc)
        flash(f'Import failed: {exc}', 'error')

    return redirect(url_for('teacher.attendance_report', course_id=course_id))


@bp.route('/grades/<int:course_id>', methods=['GET', 'POST'])
@login_required
@teacher_required
def manage_grades(course_id):
    course = _get_teacher_course(course_id)
    if not course:
        flash('Access denied.', 'error')
        return redirect(url_for('teacher.dashboard'))

    enrollments = (
        db.session.query(Enrollment, Student)
        .join(Student, Enrollment.student_id == Student.id)
        .filter(Enrollment.course_id == course_id)
        .all()
    )
    form = GradeForm()
    form.student_id.choices = [(s.id, s.full_name) for _, s in enrollments]

    if form.validate_on_submit():
        try:
            grade = Grade(
                course_id=course_id,
                student_id=form.student_id.data,
                assignment_name=form.assignment_name.data.strip(),
                grade_value=form.grade_value.data,
                max_points=form.max_points.data or 100.0,
                assignment_type=form.assignment_type.data or None,
                due_date=form.due_date.data,
                notes=form.notes.data.strip() or None,
            )
            db.session.add(grade)
            log_action(current_user.id, 'grade.create', 'grade', None)
            db.session.commit()
            flash('Grade added!', 'success')
            return redirect(url_for('teacher.manage_grades', course_id=course_id))
        except Exception as exc:
            db.session.rollback()
            logger.error('Grade error: %s', exc)
            flash('Could not add grade (duplicate assignment?).', 'error')

    grades = Grade.query.filter_by(course_id=course_id).order_by(
        Grade.assignment_name, Grade.created_at
    ).all()
    student_grades = {}
    for grade in grades:
        student_grades.setdefault(grade.student_id, []).append(grade)

    return render_template(
        'gradebook.html',
        course=course,
        enrollments=enrollments,
        student_grades=student_grades,
        grades=grades,
        form=form,
    )


@bp.route('/grades/<int:grade_id>/edit', methods=['GET', 'POST'])
@login_required
@teacher_required
def edit_grade(grade_id):
    grade = Grade.query.get_or_404(grade_id)
    if not _get_teacher_course(grade.course_id):
        flash('Access denied.', 'error')
        return redirect(url_for('teacher.dashboard'))

    enrollments = (
        db.session.query(Enrollment, Student)
        .join(Student, Enrollment.student_id == Student.id)
        .filter(Enrollment.course_id == grade.course_id)
        .all()
    )
    form = GradeForm(obj=grade)
    form.student_id.choices = [(s.id, s.full_name) for _, s in enrollments]

    if form.validate_on_submit():
        grade.student_id = form.student_id.data
        grade.assignment_name = form.assignment_name.data.strip()
        grade.grade_value = form.grade_value.data
        grade.max_points = form.max_points.data or 100.0
        grade.assignment_type = form.assignment_type.data or None
        grade.due_date = form.due_date.data
        grade.notes = form.notes.data.strip() or None
        log_action(current_user.id, 'grade.update', 'grade', grade.id)
        db.session.commit()
        flash('Grade updated.', 'success')
        return redirect(url_for('teacher.manage_grades', course_id=grade.course_id))

    return render_template('grade_edit.html', form=form, grade=grade, course=grade.course)


@bp.route('/grades/<int:grade_id>/delete', methods=['POST'])
@login_required
@teacher_required
def delete_grade(grade_id):
    grade = Grade.query.get_or_404(grade_id)
    if not _get_teacher_course(grade.course_id):
        flash('Access denied.', 'error')
        return redirect(url_for('teacher.dashboard'))
    course_id = grade.course_id
    db.session.delete(grade)
    log_action(current_user.id, 'grade.delete', 'grade', grade_id)
    db.session.commit()
    flash('Grade deleted.', 'success')
    return redirect(url_for('teacher.manage_grades', course_id=course_id))
