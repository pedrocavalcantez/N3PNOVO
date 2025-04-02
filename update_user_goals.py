from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    users = User.query.all()
    for user in users:
        user.update_goals()
    db.session.commit()
    print("Updated nutrition goals for all users successfully!")
