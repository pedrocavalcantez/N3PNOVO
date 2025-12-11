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
            socket.setdefaulttimeout(30)  # 30 second timeout (increased for Render)
            
            # Verify mail configuration before attempting to send
            mail_server = current_app.config.get('MAIL_SERVER')
            mail_port = current_app.config.get('MAIL_PORT')
            current_app.logger.info(f"Attempting to send email via {mail_server}:{mail_port}")
            
            msg = Message(subject, sender=sender, recipients=recipients)
            msg.body = text_body
            msg.html = html_body
            
            mail.send(msg)
            current_app.logger.info(f"Email sent successfully to {recipients}")
            return True
        except socket.timeout:
            current_app.logger.error(f"Email sending timeout for {recipients} (server: {current_app.config.get('MAIL_SERVER')})")
            return False
        except smtplib.SMTPAuthenticationError as e:
            current_app.logger.error(
                f"SMTP Authentication error for {recipients}: {str(e)}. "
                f"Check MAIL_USERNAME and MAIL_PASSWORD are correct."
            )
            return False
        except smtplib.SMTPException as e:
            error_msg = str(e)
            if "Connection unexpectedly closed" in error_msg:
                current_app.logger.error(
                    f"SMTP connection closed for {recipients}. "
                    f"This usually means: "
                    f"1) The sender email ({sender}) is not verified in SendGrid, OR "
                    f"2) The API Key is incorrect, OR "
                    f"3) The API Key doesn't have 'Mail Send' permissions. "
                    f"Server: {current_app.config.get('MAIL_SERVER')}:{current_app.config.get('MAIL_PORT')}"
                )
            else:
                current_app.logger.error(
                    f"SMTP error sending email to {recipients}: {str(e)}. "
                    f"Server: {current_app.config.get('MAIL_SERVER')}:{current_app.config.get('MAIL_PORT')}"
                )
            return False
        except OSError as e:
            # Network unreachable - common on Render with Gmail
            error_msg = str(e)
            if "Network is unreachable" in error_msg or "101" in error_msg:
                current_app.logger.error(
                    f"Network unreachable error for {recipients}. "
                    f"This is a common issue on Render when using Gmail SMTP. "
                    f"Consider using SendGrid, Mailgun, or another email service that works better with Render. "
                    f"Server attempted: {current_app.config.get('MAIL_SERVER')}:{current_app.config.get('MAIL_PORT')}"
                )
            else:
                current_app.logger.error(
                    f"Network error sending email to {recipients}: {str(e)}. "
                    f"Server: {current_app.config.get('MAIL_SERVER')}:{current_app.config.get('MAIL_PORT')}"
                )
            return False
        except Exception as e:
            current_app.logger.error(
                f"Unexpected error sending email to {recipients}: {str(e)}", 
                exc_info=True
            )
            return False
        finally:
            # Reset timeout
            socket.setdefaulttimeout(None)


def send_email(subject, sender, recipients, text_body, html_body, async_send=True):
    """Send an email, optionally asynchronously to avoid blocking"""
    # Check if email is configured
    mail_username = current_app.config.get('MAIL_USERNAME')
    mail_password = current_app.config.get('MAIL_PASSWORD')
    
    if not mail_username or not mail_password:
        current_app.logger.error(
            f"Email not configured. MAIL_USERNAME: {'SET' if mail_username else 'MISSING'}, "
            f"MAIL_PASSWORD: {'SET' if mail_password else 'MISSING'}. Email sending disabled."
        )
        return False
    
    if not sender:
        sender = current_app.config.get('MAIL_DEFAULT_SENDER')
        if not sender:
            current_app.logger.error("No email sender configured")
            return False
    
    # Log email configuration (without sensitive data)
    current_app.logger.info(
        f"Email config - Server: {current_app.config.get('MAIL_SERVER')}, "
        f"Port: {current_app.config.get('MAIL_PORT')}, "
        f"TLS: {current_app.config.get('MAIL_USE_TLS')}, "
        f"Sender: {sender}"
    )
    
    # For production (Render), send asynchronously to avoid worker timeout
    if async_send:
        app_context = current_app.app_context()
        # Use a result container to track success/failure
        result_container = {'success': False, 'error': None}
        
        def _send_with_result(*args, **kwargs):
            try:
                result = _send_email_sync(*args, **kwargs)
                result_container['success'] = result
            except Exception as e:
                result_container['error'] = str(e)
                result_container['success'] = False
        
        thread = threading.Thread(
            target=_send_with_result,
            args=(subject, sender, recipients, text_body, html_body, app_context),
            daemon=True
        )
        thread.start()
        
        # Wait longer to catch connection errors (especially for SMTP connection issues)
        # Most SMTP errors happen quickly, so 5 seconds should be enough
        thread.join(timeout=5)
        
        # Check for errors first
        if result_container['error']:
            current_app.logger.error(f"Email sending failed: {result_container['error']}")
            return False
        
        # Check if we got a result
        if 'success' in result_container and result_container['success'] is not None:
            if result_container['success']:
                current_app.logger.info(f"Email sent successfully to {recipients}")
                return True
            else:
                current_app.logger.error(f"Email sending failed for {recipients}")
                return False
        
        # If we're here, the thread is still running (took more than 5 seconds)
        # This is unusual for SMTP - usually means connection is hanging
        # For local dev, wait a bit more; for production, log and return optimistically
        is_local = 'localhost' in current_app.config.get('APP_URL', '') or '127.0.0.1' in current_app.config.get('APP_URL', '')
        if is_local:
            # Local: wait a bit more to catch errors
            thread.join(timeout=3)
            if result_container.get('error'):
                current_app.logger.error(f"Email sending failed: {result_container['error']}")
                return False
            if result_container.get('success') is False:
                current_app.logger.error(f"Email sending failed for {recipients}")
                return False
            if result_container.get('success') is True:
                return True
            # Still no result - connection is hanging
            current_app.logger.warning(f"Email sending is taking longer than expected for {recipients}")
            return False
        else:
            # Production: return optimistically, email will be sent in background
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

