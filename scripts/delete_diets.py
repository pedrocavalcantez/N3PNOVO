from app import create_app, db
from app.models import Diet

app = create_app()


def delete_all_diets():
    with app.app_context():
        try:
            # Delete all diets
            num_deleted = Diet.query.delete()
            db.session.commit()
            print(f"Successfully deleted {num_deleted} diets from the database.")
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting diets: {str(e)}")


if __name__ == "__main__":
    delete_all_diets()
