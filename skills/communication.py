"""
Wednesday - Communication Skill
Send emails via SMTP.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os


def send_email(to: str = "", subject: str = "", body: str = "") -> str:
    """
    Send an email using SMTP.
    Requires EMAIL_ADDRESS and EMAIL_PASSWORD in environment or .env.
    """
    sender_email = os.getenv("EMAIL_ADDRESS", "")
    sender_password = os.getenv("EMAIL_PASSWORD", "")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))

    if not sender_email or not sender_password:
        return (
            "Email is not configured. Please set EMAIL_ADDRESS and "
            "EMAIL_PASSWORD in your .env file."
        )

    if not to:
        return "Please specify a recipient email address."
    if not subject:
        subject = "Message from Wednesday Assistant"
    if not body:
        return "Please specify the email body."

    try:
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)

        return f"Email sent to {to}."
    except Exception as e:
        return f"Failed to send email: {e}"
