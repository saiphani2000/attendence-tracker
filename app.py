import os
from datetime import date
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, func, UniqueConstraint
from werkzeug.security import generate_password_hash, check_password_hash

# -------------------------------------------------
# App and DB setup
# -------------------------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

ATTENDANCE_STATUSES = ['Present', 'Absent', 'Late', 'Excused']

# -------------------------------------------------
# Models
# -------------------------------------------------
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    __table_args__ = (
        CheckConstraint("role in ('teacher','student')", name='ck_users_role'),
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    code = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)


class Enrollment(db.Model):
    __tablename__ = 'enrollments'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    __table_args__ = (
        UniqueConstraint('course_id', 'student_id', name='uq_enrollments_course_student'),
    )


class Session(db.Model):
    __tablename__ = 'sessions'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD
    topic = db.Column(db.String(255))


class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(20), nullable=False)

    __table_args__ = (
        UniqueConstraint('session_id', 'student_id', name='uq_attendance_session_student'),
        CheckConstraint("status in ('Present','Absent','Late','Excused')", name='ck_attendance_status'),
    )


# -------------------------------------------------
# Auth helpers
# -------------------------------------------------

def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login_teacher'))
        return view_func(*args, **kwargs)
    return wrapped


def role_required(role):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if session.get('role') != role:
                flash('Unauthorized access.', 'error')
                return redirect(url_for('login_teacher'))
            return view_func(*args, **kwargs)
        return wrapped
    return decorator


def current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)


# -------------------------------------------------
# Initial data for quick start
# -------------------------------------------------

def ensure_database():
    # Create tables
    db.create_all()

    # Seed demo accounts if missing
    if User.query.count() == 0:
        teacher = User(name='Alice Teacher', email='teacher1@example.com', role='teacher', password_hash='')
        teacher.set_password('password123')
        student = User(name='Bob Student', email='student1@example.com', role='student', password_hash='')
        student.set_password('password123')
        db.session.add_all([teacher, student])
        db.session.commit()

        # Create a demo course and enroll the student
        course = Course(name='Intro to Flask', code='FLK101', teacher_id=teacher.id)
        db.session.add(course)
        db.session.commit()

        enrollment = Enrollment(course_id=course.id, student_id=student.id)
        db.session.add(enrollment)
        db.session.commit()

        # Create a demo session and mark attendance
        sess = Session(course_id=course.id, date=str(date.today()), topic='Getting Started')
        db.session.add(sess)
        db.session.commit()

        att = Attendance(session_id=sess.id, student_id=student.id, status='Present')
        db.session.add(att)
        db.session.commit()


# -------------------------------------------------
# Routes: general
# -------------------------------------------------
@app.route('/')
def index():
    if session.get('role') == 'teacher':
        return redirect(url_for('teacher_dashboard'))
    if session.get('role') == 'student':
        return redirect(url_for('student_dashboard'))
    return redirect(url_for('login_teacher'))


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login_teacher'))


# -------------------------------------------------
# Routes: login
# -------------------------------------------------
@app.route('/login/teacher', methods=['GET', 'POST'])
def login_teacher():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email, role='teacher').first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['role'] = user.role
            flash('Welcome back!', 'success')
            return redirect(url_for('teacher_dashboard'))
        flash('Invalid credentials.', 'error')
    return render_template('login_teacher.html', title='Teacher Login')


@app.route('/login/student', methods=['GET', 'POST'])
def login_student():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email, role='student').first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['role'] = user.role
            flash('Welcome back!', 'success')
            return redirect(url_for('student_dashboard'))
        flash('Invalid credentials.', 'error')
    return render_template('login_student.html', title='Student Login')


# -------------------------------------------------
# Routes: teacher - courses & enrollments
# -------------------------------------------------
@app.route('/courses', methods=['GET', 'POST'])
@login_required
@role_required('teacher')
def courses():
    user = current_user()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip()
        if not name or not code:
            flash('Course name and code are required.', 'error')
        else:
            course = Course(name=name, code=code, teacher_id=user.id)
            db.session.add(course)
            db.session.commit()
            flash('Course created.', 'success')
            return redirect(url_for('courses'))

    teacher_courses = Course.query.filter_by(teacher_id=user.id).order_by(Course.name.asc()).all()
    # For each course, provide enrolled count and sessions count
    course_infos = []
    for c in teacher_courses:
        enrolled_count = Enrollment.query.filter_by(course_id=c.id).count()
        sessions_count = Session.query.filter_by(course_id=c.id).count()
        course_infos.append({'course': c, 'enrolled_count': enrolled_count, 'sessions_count': sessions_count})
    return render_template('courses.html', title='Courses', courses=course_infos)


@app.route('/courses/<int:course_id>/enroll', methods=['GET', 'POST'])
@login_required
@role_required('teacher')
def enroll(course_id):
    user = current_user()
    course = Course.query.filter_by(id=course_id, teacher_id=user.id).first_or_404()
    if request.method == 'POST':
        student_email = request.form.get('student_email', '').strip().lower()
        student_id = request.form.get('student_id', '').strip()
        student = None
        if student_id:
            student = User.query.filter_by(id=student_id, role='student').first()
        if not student and student_email:
            student = User.query.filter_by(email=student_email, role='student').first()
        if not student:
            flash('Student not found. Please ensure the student account exists.', 'error')
            return redirect(url_for('enroll', course_id=course.id))
        # Create enrollment if not exists
        existing = Enrollment.query.filter_by(course_id=course.id, student_id=student.id).first()
        if existing:
            flash('Student already enrolled.', 'warning')
        else:
            db.session.add(Enrollment(course_id=course.id, student_id=student.id))
            db.session.commit()
            flash('Student enrolled successfully.', 'success')
        return redirect(url_for('courses'))

    enrolled = db.session.query(User).join(Enrollment, Enrollment.student_id == User.id).filter(Enrollment.course_id == course.id).order_by(User.name.asc()).all()
    return render_template('enroll.html', title='Enroll Students', course=course, enrolled=enrolled)


# -------------------------------------------------
# Routes: teacher - sessions & attendance
# -------------------------------------------------
@app.route('/courses/<int:course_id>/sessions/create', methods=['GET', 'POST'])
@login_required
@role_required('teacher')
def create_session(course_id):
    user = current_user()
    course = Course.query.filter_by(id=course_id, teacher_id=user.id).first_or_404()
    if request.method == 'POST':
        d = request.form.get('date', '').strip() or str(date.today())
        topic = request.form.get('topic', '').strip() or None
        sess = Session(course_id=course.id, date=d, topic=topic)
        db.session.add(sess)
        db.session.commit()
        flash('Session created. You can now mark attendance.', 'success')
        return redirect(url_for('mark_attendance', course_id=course.id, session_id=sess.id))
    return render_template('create_session.html', title='Create Session', course=course, today=str(date.today()))


@app.route('/courses/<int:course_id>/sessions/<int:session_id>/attendance', methods=['GET', 'POST'])
@login_required
@role_required('teacher')
def mark_attendance(course_id, session_id):
    user = current_user()
    course = Course.query.filter_by(id=course_id, teacher_id=user.id).first_or_404()
    sess = Session.query.filter_by(id=session_id, course_id=course.id).first_or_404()

    enrolled_students = db.session.query(User).join(Enrollment, Enrollment.student_id == User.id).filter(Enrollment.course_id == course.id).order_by(User.name.asc()).all()

    if request.method == 'POST':
        # Expect fields like status_<student_id>
        for student in enrolled_students:
            status_key = f'status_{student.id}'
            status_val = request.form.get(status_key)
            if status_val not in ATTENDANCE_STATUSES:
                continue
            row = Attendance.query.filter_by(session_id=sess.id, student_id=student.id).first()
            if row:
                row.status = status_val
            else:
                db.session.add(Attendance(session_id=sess.id, student_id=student.id, status=status_val))
        db.session.commit()
        flash('Attendance saved.', 'success')
        return redirect(url_for('mark_attendance', course_id=course.id, session_id=sess.id))

    # Existing attendance map
    existing = Attendance.query.filter_by(session_id=sess.id).all()
    existing_map = {a.student_id: a.status for a in existing}

    return render_template('attendance_form.html', title='Mark Attendance', course=course, sess=sess, students=enrolled_students, statuses=ATTENDANCE_STATUSES, existing=existing_map)


# -------------------------------------------------
# Routes: dashboards and reports
# -------------------------------------------------
@app.route('/teacher_dashboard')
@login_required
@role_required('teacher')
def teacher_dashboard():
    user = current_user()

    # Teacher-wide stats
    teacher_course_ids = [c.id for c in Course.query.filter_by(teacher_id=user.id).all()]
    total_sessions = Session.query.filter(Session.course_id.in_(teacher_course_ids)).count() if teacher_course_ids else 0

    # Distinct enrolled students across teacher's courses
    total_students = db.session.query(func.count(func.distinct(Enrollment.student_id))).filter(Enrollment.course_id.in_(teacher_course_ids)).scalar() if teacher_course_ids else 0

    # Attendance percentage summaries
    if teacher_course_ids:
        session_ids = [s.id for s in Session.query.with_entities(Session.id).filter(Session.course_id.in_(teacher_course_ids)).all()]
    else:
        session_ids = []

    status_counts = {k: 0 for k in ATTENDANCE_STATUSES}
    total_att_recs = 0
    if session_ids:
        rows = db.session.query(Attendance.status, func.count(Attendance.id)).filter(Attendance.session_id.in_(session_ids)).group_by(Attendance.status).all()
        for st, cnt in rows:
            status_counts[st] = cnt
        total_att_recs = sum(status_counts.values())

    def pct(val, total):
        return round((val / total) * 100, 1) if total else 0.0

    summary = {
        'present_pct': pct(status_counts['Present'], total_att_recs),
        'absent_pct': pct(status_counts['Absent'], total_att_recs),
        'late_pct': pct(status_counts['Late'], total_att_recs),
        'excused_pct': pct(status_counts['Excused'], total_att_recs),
    }

    # List of courses with links to manage
    courses = Course.query.filter_by(teacher_id=user.id).order_by(Course.name.asc()).all()

    return render_template('teacher_dashboard.html', title='Teacher Dashboard', total_sessions=total_sessions, total_students=total_students, summary=summary, courses=courses)


@app.route('/courses/<int:course_id>/report')
@login_required
@role_required('teacher')
def course_report(course_id):
    user = current_user()
    course = Course.query.filter_by(id=course_id, teacher_id=user.id).first_or_404()

    # Get enrolled students
    students = db.session.query(User).join(Enrollment, Enrollment.student_id == User.id).filter(Enrollment.course_id == course.id).order_by(User.name.asc()).all()

    # Get session ids
    session_ids = [s.id for s in Session.query.with_entities(Session.id).filter_by(course_id=course.id).all()]

    # Build stats per student
    rows = []
    for s in students:
        counts = {k: 0 for k in ATTENDANCE_STATUSES}
        total = 0
        if session_ids:
            q = db.session.query(Attendance.status, func.count(Attendance.id)).filter(Attendance.session_id.in_(session_ids), Attendance.student_id == s.id).group_by(Attendance.status).all()
            for st, cnt in q:
                counts[st] = cnt
            total = sum(counts.values())
        attendance_pct = 0.0
        denom = counts['Present'] + counts['Absent'] + counts['Late'] + counts['Excused']
        if denom:
            attendance_pct = round(((counts['Present'] + 0.5 * counts['Late']) / denom) * 100, 1)
        rows.append({
            'student': s,
            'present': counts['Present'],
            'absent': counts['Absent'],
            'late': counts['Late'],
            'excused': counts['Excused'],
            'attendance_pct': attendance_pct,
            'total': total,
        })

    return render_template('course_report.html', title=f"Report - {course.name}", course=course, rows=rows)


@app.route('/student_dashboard')
@login_required
@role_required('student')
def student_dashboard():
    user = current_user()

    # Get student's courses
    courses = db.session.query(Course).join(Enrollment, Enrollment.course_id == Course.id).filter(Enrollment.student_id == user.id).order_by(Course.name.asc()).all()

    # For each course, compute metrics
    course_rows = []
    for c in courses:
        session_ids = [s.id for s in Session.query.with_entities(Session.id).filter_by(course_id=c.id).all()]
        counts = {k: 0 for k in ATTENDANCE_STATUSES}
        if session_ids:
            q = db.session.query(Attendance.status, func.count(Attendance.id)).filter(Attendance.session_id.in_(session_ids), Attendance.student_id == user.id).group_by(Attendance.status).all()
            for st, cnt in q:
                counts[st] = cnt
        denom = counts['Present'] + counts['Absent'] + counts['Late'] + counts['Excused']
        attendance_pct = round(((counts['Present'] + 0.5 * counts['Late']) / denom) * 100, 1) if denom else 0.0
        course_rows.append({
            'course': c,
            'present': counts['Present'],
            'absent': counts['Absent'],
            'late': counts['Late'],
            'excused': counts['Excused'],
            'attendance_pct': attendance_pct,
        })

    return render_template('student_dashboard.html', title='Student Dashboard', rows=course_rows)


# -------------------------------------------------
# App run
# -------------------------------------------------
if __name__ == '__main__':
    ensure_database()
    app.run(host='0.0.0.0', port=5000, debug=True)
