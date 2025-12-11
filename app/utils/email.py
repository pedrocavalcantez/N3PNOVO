from flask import render_template, current_app, request, has_request_context
from flask_mail import Message
from app import mail
import socket
import threading
import smtplib
import os
import requests


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


def _send_email_via_sendgrid_api(subject, sender, recipients, text_body, html_body):
    """Send email using SendGrid REST API (more reliable than SMTP on Render)"""
    api_key = current_app.config.get('MAIL_PASSWORD')
    if not api_key or not api_key.startswith('SG.'):
        current_app.logger.error("SendGrid API key not found or invalid format")
        return False
    
    url = "https://api.sendgrid.com/v3/mail/send"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Prepare email data
    email_data = {
        "personalizations": [{
            "to": [{"email": email} for email in recipients]
        }],
        "from": {"email": sender},
        "subject": subject,
        "content": [
            {
                "type": "text/plain",
                "value": text_body
            },
            {
                "type": "text/html",
                "value": html_body
            }
        ]
    }
    
    try:
        response = requests.post(url, json=email_data, headers=headers, timeout=10)
        if response.status_code == 202:
            current_app.logger.info(f"Email sent successfully via SendGrid API to {recipients}")
            return True
        else:
            current_app.logger.error(
                f"SendGrid API error: {response.status_code} - {response.text}. "
                f"Recipients: {recipients}"
            )
            return False
    except requests.exceptions.Timeout:
        current_app.logger.error(f"SendGrid API timeout for {recipients}")
        return False
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"SendGrid API request error for {recipients}: {str(e)}")
        return False
    except Exception as e:
        current_app.logger.error(f"Unexpected error using SendGrid API for {recipients}: {str(e)}", exc_info=True)
        return False


def send_email(subject, sender, recipients, text_body, html_body, async_send=True, use_api=False):
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
    
    # Check if we should use SendGrid API instead of SMTP
    # API is more reliable on Render (avoids SMTP timeout issues)
    mail_server = current_app.config.get('MAIL_SERVER', '')
    is_sendgrid = 'sendgrid' in mail_server.lower()
    is_render_env = os.environ.get('RENDER') is not None or 'render.com' in current_app.config.get('APP_URL', '').lower()
    
    # Use API if explicitly requested, or automatically if using SendGrid on Render
    # This avoids SMTP timeout issues on Render
    should_use_api = use_api or (is_sendgrid and is_render_env)
    
    if should_use_api:
        current_app.logger.info(f"Using SendGrid API to send email to {recipients} (more reliable than SMTP on Render)")
        if async_send:
            # For async, run in thread
            app_context = current_app.app_context()
            result_container = {'success': False, 'error': None}
            
            def _send_api():
                try:
                    with app_context:
                        result_container['success'] = _send_email_via_sendgrid_api(
                            subject, sender, recipients, text_body, html_body
                        )
                except Exception as e:
                    result_container['error'] = str(e)
                    result_container['success'] = False
            
            thread = threading.Thread(target=_send_api, daemon=True)
            thread.start()
            thread.join(timeout=15)
            
            if result_container.get('error'):
                current_app.logger.error(f"SendGrid API error: {result_container['error']}")
                return False
            return result_container.get('success', False)
        else:
            return _send_email_via_sendgrid_api(subject, sender, recipients, text_body, html_body)
    
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
                # Log error in thread context for better debugging
                from flask import current_app
                current_app.logger.error(
                    f"Exception in email sending thread: {str(e)}",
                    exc_info=True
                )
                result_container['error'] = str(e)
                result_container['success'] = False
        
        thread = threading.Thread(
            target=_send_with_result,
            args=(subject, sender, recipients, text_body, html_body, app_context),
            daemon=True
        )
        thread.start()
        
        # Wait longer to catch connection errors (especially for SMTP connection issues)
        # On Render, SMTP connections can be slower, so we wait longer
        is_render = os.environ.get('RENDER') is not None or 'render.com' in current_app.config.get('APP_URL', '').lower()
        wait_timeout = 20 if is_render else 10  # 20 seconds on Render, 10 locally
        current_app.logger.info(f"Waiting up to {wait_timeout} seconds for email to send...")
        thread.join(timeout=wait_timeout)
        
        # Check for errors first
        if result_container['error']:
            current_app.logger.error(
                f"Email sending failed for {recipients}. Error: {result_container['error']}. "
                f"Check logs above for full traceback."
            )
            return False
        
        # Check if we got a result
        if 'success' in result_container and result_container['success'] is not None:
            if result_container['success']:
                current_app.logger.info(f"Email sent successfully to {recipients}")
                return True
            else:
                current_app.logger.error(
                    f"Email sending failed for {recipients}. "
                    f"This might indicate: sender not verified, API key issues, or network problems."
                )
                return False
        
        # If we're here, the thread is still running (took longer than wait_timeout)
        # This is unusual for SMTP - usually means connection is hanging or very slow
        if is_render:
            # On Render, if it's taking this long, it's likely a network issue
            # Log warning but return optimistically - email might still be sent in background
            current_app.logger.warning(
                f"Email sending is taking longer than {wait_timeout} seconds for {recipients}. "
                f"This might indicate network issues. Email may still be sent in background."
            )
            return True  # Return optimistically on Render
        else:
            # Local: wait a bit more to catch errors
            thread.join(timeout=5)
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

