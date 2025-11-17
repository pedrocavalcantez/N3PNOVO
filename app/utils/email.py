from flask import render_template, current_app
from flask_mail import Message
from app import mail


def send_email(subject, sender, recipients, text_body, html_body):
    """Send an email"""
    # Check if email is configured
    if not current_app.config.get('MAIL_USERNAME') or not current_app.config.get('MAIL_PASSWORD'):
        current_app.logger.warning("Email not configured (MAIL_USERNAME or MAIL_PASSWORD missing). Email sending disabled.")
        return False
    
    if not sender:
        sender = current_app.config.get('MAIL_DEFAULT_SENDER')
        if not sender:
            current_app.logger.error("No email sender configured")
            return False
    
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    try:
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Error sending email: {str(e)}")
        return False


def send_confirmation_email(user, token):
    """Send email confirmation email to user"""
    confirmation_url = f"{current_app.config['APP_URL']}/auth/confirm_email/{token}"
    
    subject = "Confirme seu email - N3P"
    
    text_body = f"""
Olá {user.nome},

Obrigado por se cadastrar no N3P!

Por favor, confirme seu email clicando no link abaixo:

{confirmation_url}

Este link expira em 24 horas.

Se você não se cadastrou nesta conta, pode ignorar este email.

Atenciosamente,
Equipe N3P
"""
    
    html_body = render_template('auth/email/confirm_email.html', 
                               user=user, 
                               confirmation_url=confirmation_url)
    
    return send_email(
        subject=subject,
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email],
        text_body=text_body,
        html_body=html_body
    )


def send_password_reset_email(user, token):
    """Send password reset email to user"""
    reset_url = f"{current_app.config['APP_URL']}/auth/reset_password/{token}"
    
    subject = "Redefinir sua senha - N3P"
    
    text_body = f"""
Olá {user.nome},

Recebemos uma solicitação para redefinir a senha da sua conta no N3P.

Para redefinir sua senha, clique no link abaixo:

{reset_url}

Este link expira em 1 hora.

Se você não solicitou a redefinição de senha, pode ignorar este email. Sua senha permanecerá inalterada.

Atenciosamente,
Equipe N3P
"""
    
    html_body = render_template('auth/email/reset_password.html', 
                               user=user, 
                               reset_url=reset_url)
    
    return send_email(
        subject=subject,
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email],
        text_body=text_body,
        html_body=html_body
    )

