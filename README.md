# Student Attendance & Performance Tracker (Flask)

A simple full-stack web application to track student attendance and basic performance summaries.

## Tech Stack
- Backend: Flask (Python)
- Frontend: HTML, CSS, JavaScript, Bootstrap 5
- Database: SQLite (file: `database.db`)

## Features (implemented)
- Login system with separate pages for teachers and students
- Password hashing using Werkzeug
- Role-based navigation and access using Flask sessions
- Teacher course management: create courses, view courses
- Enroll students by email or user ID
- Create class sessions (date, optional topic)
- Mark attendance per enrolled student with Present / Absent / Late / Excused
- Teacher Dashboard: total sessions, total students, and attendance percentage summary
- Course Report (teacher): per-student counts and Attendance % with sortable columns
- Student Dashboard: per-course counts and attendance percentage, sortable
- Bootstrap UI, navbar, and dismissible success/error alerts

## Not in scope (optional for future)
- CSV export for attendance reports
- Charts (Chart.js) for visualizations

## Quick Start

Requirements: Python 3.9+

1) Install dependencies
```bash
pip install flask flask_sqlalchemy
```

2) Run the app
```bash
python app.py
```

3) Open in browser
- http://localhost:5000

4) Demo accounts (auto-seeded on first run)
- Teacher: `teacher1@example.com` / `password123`
- Student: `student1@example.com` / `password123`

## Environment
- `SECRET_KEY`: optional; defaults to a dev key
  - Example: `export SECRET_KEY="change-me"`

## Folder Structure
```
/app.py                 # Flask app entry point
/templates/            # Jinja2 templates
  base.html
  login_teacher.html
  login_student.html
  teacher_dashboard.html
  student_dashboard.html
  courses.html
  enroll.html
  create_session.html
  attendance_form.html
  course_report.html
/static/css/styles.css  # Custom styles
/static/js/main.js      # Table sorting and misc JS
/schema.sql             # DB schema (reference)
/database.db            # Auto-created at runtime
```

## Data Model
Tables:
- users(id, name, email, password_hash, role)
- courses(id, name, code, teacher_id)
- enrollments(id, course_id, student_id)
- sessions(id, course_id, date, topic)
- attendance(id, session_id, student_id, status)

Status values: `Present`, `Absent`, `Late`, `Excused`

Attendance % formula: `(Present + 0.5×Late) / (Present + Absent + Late + Excused) × 100`

## Notes
- DB is created via SQLAlchemy `create_all()` on first run; `schema.sql` provided for reference.
- Course/session ownership checks ensure teachers can only manage their own data.
- All tables with counts are sortable by clicking column headers.
