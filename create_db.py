from app import create_app, db

app = create_app()

with app.app_context():
    # Drop all tables if they exist
    db.drop_all()
    # Create all tables
    db.create_all()
    print("Database tables created successfully!")
