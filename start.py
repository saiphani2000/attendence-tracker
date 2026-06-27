#!/usr/bin/env python3
"""Initialize database and start Gunicorn."""
import os
import sys


def main():
    sys.stdout.flush()
    print('Initializing database...', flush=True)

    from app import create_app, seed_demo_data
    from app.extensions import db

    app = create_app()
    with app.app_context():
        db.create_all()
        seed_demo_data()
    print('Database ready.', flush=True)

    print('Starting Gunicorn...', flush=True)
    if os.path.exists('gunicorn_config.py'):
        os.execvp('gunicorn', ['gunicorn', '-c', 'gunicorn_config.py', 'wsgi:app'])
    else:
        os.execvp('gunicorn', [
            'gunicorn', '--bind', '0.0.0.0:5000',
            '--workers', '4', '--timeout', '120', 'wsgi:app',
        ])


if __name__ == '__main__':
    main()
