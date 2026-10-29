"""Plain-text email over SMTP; in development Mailpit catches every message."""

import smtplib
from email.message import EmailMessage

from app.config import Settings


def send_mail(settings: Settings, to: str, subject: str, body: str) -> None:
    """Send one message; log in over STARTTLS only when a user is configured."""
    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        if settings.smtp_user:
            smtp.starttls()
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(message)
