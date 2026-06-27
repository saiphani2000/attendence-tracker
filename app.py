"""Backward-compatible entry point."""
from app import create_app

app = create_app()

# Legacy alias for scripts that import init_db
def init_db():
    from app.extensions import db
    from app import seed_demo_data
    db.create_all()
    seed_demo_data()

if __name__ == '__main__':
    import os
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=5000)
