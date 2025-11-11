# This script is used by Render to initialize the database tables.
from app import app, db

with app.app_context():
    print("Creating database tables...")
    db.create_all()
    print("Tables created successfully.")
