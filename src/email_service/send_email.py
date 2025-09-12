import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv


load_dotenv()

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))


def send_email(receiver_email: str, subject: str, plain_body: str, html_body: str, attachments=None) -> bool:
    """
    Send an email with optional attachments.
    """
    try:
        message = MIMEMultipart("alternative")
        message["From"] = EMAIL_SENDER
        message["To"] = receiver_email
        message["Subject"] = subject

        # Plain + HTML parts
        message.attach(MIMEText(plain_body, "plain"))
        message.attach(MIMEText(html_body, "html"))

        # Attachments
        if attachments:
            for file_bytes, filename in attachments:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(file_bytes)
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename={filename}")
                message.attach(part)

        # Secure connection
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, receiver_email, message.as_string())

        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False


def send_no_logs_email(receiver_email: str, date: str) -> bool:
    subject = f"No Logs Available - {date}"
    plain_body = f"No logs were generated for {date}."
    html_body = f"<html><body><h2>No Logs Available</h2><p>No logs were generated for {date}.</p></body></html>"
    return send_email(receiver_email, subject, plain_body, html_body)


def send_notification_email(receiver_email: str, message: str) -> bool:
    subject = "Notification - Divinely Bot"
    plain_body = f"Notification:\n\n{message}"
    html_body = f"<html><body><h2>Notification - Divinely Bot</h2><p>{message}</p></body></html>"
    return send_email(receiver_email, subject, plain_body, html_body)


