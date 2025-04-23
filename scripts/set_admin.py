import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app, db
from app.models import User


def set_user_as_admin(username):
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if user:
            user.admin = True
            db.session.commit()
            print(f"User {username} is now an admin")
        else:
            print(f"User {username} not found")


if __name__ == "__main__":
    import sys

    set_user_as_admin("admin")
    # if len(sys.argv) != 2:
    #     print("Usage: python set_admin.py <username>")
    #     sys.exit(1)
    # set_user_as_admin(sys.argv[1])
