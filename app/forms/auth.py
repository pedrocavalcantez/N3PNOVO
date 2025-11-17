from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    FloatField,
    SelectField,
    IntegerField,
    SubmitField,
)
from wtforms.validators import DataRequired, Length, ValidationError, NumberRange
from app.models import User
from app.constants import ACTIVITY_FACTORS, OBJECTIVES, GENDER_CHOICES

# Create display name mappings for activity factors and objectives
ACTIVITY_DISPLAY = {
    "sedentario": "Sedentário",
    "leve": "Levemente Ativo",
    "moderado": "Moderadamente Ativo",
    "muito_ativo": "Muito Ativo",
    "extremamente_ativo": "Extremamente Ativo",
}

OBJECTIVE_DISPLAY = {
    "perder_peso": "Perder Peso",
    "manter_peso": "Manter Peso",
    "ganhar_peso": "Ganhar Peso",
    "ganhar_massa": "Ganhar Massa Muscular",
}


class LoginForm(FlaskForm):
    """Form for user login"""

    username = StringField(
        "Username", validators=[DataRequired(), Length(min=4, max=80)]
    )
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Entrar")


class SignupForm(FlaskForm):
    """Form for user registration"""

    username = StringField(
        "Username", validators=[DataRequired(), Length(min=4, max=80)]
    )
    email = StringField("Email", validators=[DataRequired(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), Length(min=6)]
    )
    nome = StringField("Nome", validators=[DataRequired(), Length(max=100)])
    idade = IntegerField(
        "Idade", validators=[DataRequired(), NumberRange(min=15, max=100)]
    )
    altura = FloatField(
        "Altura (metros)", validators=[DataRequired(), NumberRange(min=1.0, max=2.5)]
    )
    peso = FloatField(
        "Peso (kg)", validators=[DataRequired(), NumberRange(min=30, max=300)]
    )
    sexo = SelectField(
        "Sexo", choices=list(GENDER_CHOICES.items()), validators=[DataRequired()]
    )
    fator_atividade = SelectField(
        "Nível de Atividade",
        choices=list(ACTIVITY_DISPLAY.items()),
        validators=[DataRequired()],
    )
    objetivo = SelectField(
        "Objetivo", choices=list(OBJECTIVE_DISPLAY.items()), validators=[DataRequired()]
    )
    submit = SubmitField("Criar Conta")

    def validate_username(self, field):
        """Check if username is already taken"""
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("Este nome de usuário já está em uso.")

    def validate_email(self, field):
        """Check if email is already taken"""
        if User.query.filter_by(email=field.data).first():
            raise ValidationError("Este email já está em uso.")

    def validate_confirm_password(self, field):
        """Check if passwords match"""
        if field.data != self.password.data:
            raise ValidationError("As senhas não coincidem.")


class ForgotPasswordForm(FlaskForm):
    """Form for requesting password reset"""

    email = StringField("Email", validators=[DataRequired(), Length(max=120)])
    submit = SubmitField("Enviar Link de Redefinição")

    def validate_email(self, field):
        """Check if email exists in database"""
        if not User.query.filter_by(email=field.data).first():
            raise ValidationError("Este email não está cadastrado em nossa base de dados.")


class ResetPasswordForm(FlaskForm):
    """Form for resetting password"""

    password = PasswordField("Nova Senha", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirmar Nova Senha", validators=[DataRequired(), Length(min=6)]
    )
    submit = SubmitField("Redefinir Senha")

    def validate_confirm_password(self, field):
        """Check if passwords match"""
        if field.data != self.password.data:
            raise ValidationError("As senhas não coincidem.")


class EditProfileForm(FlaskForm):
    """Form for editing user profile"""

    nome = StringField("Nome", validators=[DataRequired(), Length(max=100)])
    idade = IntegerField(
        "Idade", validators=[DataRequired(), NumberRange(min=15, max=100)]
    )
    altura = FloatField(
        "Altura (metros)", validators=[DataRequired(), NumberRange(min=1.0, max=2.5)]
    )
    peso = FloatField(
        "Peso (kg)", validators=[DataRequired(), NumberRange(min=30, max=300)]
    )
    sexo = SelectField(
        "Sexo", choices=list(GENDER_CHOICES.items()), validators=[DataRequired()]
    )
    fator_atividade = SelectField(
        "Nível de Atividade",
        choices=list(ACTIVITY_DISPLAY.items()),
        validators=[DataRequired()],
    )
    objetivo = SelectField(
        "Objetivo", choices=list(OBJECTIVE_DISPLAY.items()), validators=[DataRequired()]
    )
    submit = SubmitField("Atualizar Perfil")
