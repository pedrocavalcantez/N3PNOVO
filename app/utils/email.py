from flask import render_template, current_app, request, has_request_context
from flask_mail import Message
from app import mail
import socket
import threading
import smtplib


def get_app_url():
    """Get the application URL, auto-detecting from request if needed"""
    app_url = current_app.config.get('APP_URL', '')
    
    # If APP_URL is not set or is localhost, try to detect from request
    if not app_url or 'localhost' in app_url or '127.0.0.1' in app_url:
        if has_request_context() and request and request.host_url:
            # Remove trailing slash
            app_url = request.host_url.rstrip('/')
            # Use https if the request was https (common on Render)
            if request.is_secure or request.headers.get('X-Forwarded-Proto') == 'https':
                app_url = app_url.replace('http://', 'https://', 1)
            current_app.logger.info(f"Auto-detected APP_URL: {app_url}")
        else:
            # Fallback to localhost if no request context
            app_url = app_url or "http://localhost:5000"
            current_app.logger.warning(f"Using fallback APP_URL: {app_url}")
    
    return app_url


def _send_email_sync(subject, sender, recipients, text_body, html_body, app_context):
    """Internal function to send email synchronously (called in thread)"""
    with app_context:
        from flask import current_app
        from app import mail
        
        try:
            # Set socket timeout to prevent hanging
            socket.setdefaulttimeout(10)  # 10 second timeout
            
            msg = Message(subject, sender=sender, recipients=recipients)
            msg.body = text_body
            msg.html = html_body
            
            mail.send(msg)
            current_app.logger.info(f"Email sent successfully to {recipients}")
            return True
        except socket.timeout:
            current_app.logger.error(f"Email sending timeout for {recipients}")
            return False
        except smtplib.SMTPException as e:
            current_app.logger.error(f"SMTP error sending email to {recipients}: {str(e)}")
            return False
        except Exception as e:
            current_app.logger.error(f"Error sending email to {recipients}: {str(e)}", exc_info=True)
            return False
        finally:
            # Reset timeout
            socket.setdefaulttimeout(None)


def send_email(subject, sender, recipients, text_body, html_body, async_send=True):
    """Send an email, optionally asynchronously to avoid blocking"""
    # Check if email is configured
    if not current_app.config.get('MAIL_USERNAME') or not current_app.config.get('MAIL_PASSWORD'):
        current_app.logger.warning("Email not configured (MAIL_USERNAME or MAIL_PASSWORD missing). Email sending disabled.")
        return False
    
    if not sender:
        sender = current_app.config.get('MAIL_DEFAULT_SENDER')
        if not sender:
            current_app.logger.error("No email sender configured")
            return False
    
    # For production (Render), send asynchronously to avoid worker timeout
    if async_send:
        app_context = current_app.app_context()
        thread = threading.Thread(
            target=_send_email_sync,
            args=(subject, sender, recipients, text_body, html_body, app_context),
            daemon=True
        )
        thread.start()
        # Return True immediately - email will be sent in background
        # In production, we assume it will work
        current_app.logger.info(f"Email sending started in background for {recipients}")
        return True
    else:
        # Synchronous sending for local development
        return _send_email_sync(subject, sender, recipients, text_body, html_body, current_app.app_context())


def send_confirmation_email(user, token):
    """Send email confirmation email to user"""
    app_url = get_app_url()
    confirmation_url = f"{app_url}/auth/confirm_email/{token}"
    
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
    app_url = get_app_url()
    reset_url = f"{app_url}/auth/reset_password/{token}"
    
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

