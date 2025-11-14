from datetime import datetime
from app import db
from .user import User


class Diet(db.Model):
    __tablename__ = "diets"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    date = db.Column(db.Date, nullable=True)  # NULL = dieta modelo, com valor = dieta do dia
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    meals_data = db.Column(db.JSON, nullable=True)

    # Unique constraint: um usuário só pode ter uma dieta por data (apenas para dietas do dia)
    # Para dietas modelo (date=NULL), pode ter múltiplas com o mesmo nome
    __table_args__ = (db.UniqueConstraint("user_id", "date", name="unique_user_diet_date"),)

    @property
    def is_template(self):
        """Retorna True se for uma dieta modelo (sem data)"""
        return self.date is None

    def __repr__(self):
        if self.date:
            return f"<Diet {self.name} - {self.date}>"
        else:
            return f"<Diet Template {self.name}>"
