from datetime import datetime
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5


class User(UserMixin, db.Model):
    """Modelo de usuário com autenticação e perfil básico."""

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        """Define a senha do usuário usando hash."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifica se a senha fornecida corresponde ao hash armazenado."""
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        """Gera URL do avatar usando Gravatar."""
        digest = md5(self.email.lower().encode("utf-8")).hexdigest()
        return f"https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}"

    def __repr__(self):
        return f"<User {self.username}>"


class MealTemplate(db.Model):
    """Modelo para templates de refeições."""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    items = db.relationship(
        "MealTemplateItem", backref="template", lazy=True, cascade="all, delete-orphan"
    )

    def add_item(self, food_code, quantity):
        """Adiciona um item ao template."""
        item = MealTemplateItem(food_code=food_code, quantity=quantity)
        self.items.append(item)
        return item

    def remove_item(self, item_id):
        """Remove um item do template."""
        item = next((i for i in self.items if i.id == item_id), None)
        if item:
            self.items.remove(item)
            return True
        return False

    def __repr__(self):
        return f"<MealTemplate {self.name}>"


class MealTemplateItem(db.Model):
    """Modelo para itens de um template de refeição."""

    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(
        db.Integer, db.ForeignKey("meal_templates.id"), nullable=False
    )
    food_code = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def update_quantity(self, new_quantity):
        """Atualiza a quantidade do item."""
        self.quantity = new_quantity
        return self

    def __repr__(self):
        return f"<MealTemplateItem {self.food_code}>"


# ... rest of the existing code ...
