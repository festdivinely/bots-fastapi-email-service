import os
import io
import logging
from logging.handlers import RotatingFileHandler
import atexit
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Tuple
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from src.email_service.send_email import send_email, send_no_logs_email, send_notification_email
from src.cron.keep_alive import keep_alive_job
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter

load_dotenv()

# Ensure logs directory exists
logs_dir = os.path.join(os.getcwd(), "logs")
os.makedirs(logs_dir, exist_ok=True)

# Configure logging with rotation
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler(
            filename=os.path.join(logs_dir, "fastapi.log"),
            maxBytes=10_000_000,  # 10MB
            backupCount=5  # Keep 5 backup files
        )
    ]
)
logger = logging.getLogger(__name__)

# Scheduler setup
def start_scheduler_with_retry(retries=3, delay=5):
    for attempt in range(retries):
        try:
            scheduler = BackgroundScheduler()
            scheduler.add_job(keep_alive_job, CronTrigger.from_crontab("*/12 * * * *"))  # Changed to 12 minutes
            scheduler.start()
            logger.info("Scheduler started successfully")
            atexit.register(lambda: logger.info("Shutting down scheduler") or scheduler.shutdown())
            return
        except Exception as e:
            logger.error(f"Failed to start scheduler (attempt {attempt + 1}/{retries})", exc_info=True)
            if attempt < retries - 1:
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logger.error("Scheduler failed to start after max retries")

start_scheduler_with_retry()

app = FastAPI(title="Divinely Bot Email Service")

class LogRequest(BaseModel):
    logContent: Optional[str] = None
    fileName: Optional[str] = "logs.pdf"
    recipientEmail: str

class NotificationEmailRequest(BaseModel):
    receiverEmail: str
    message: str

class NoLogsEmailRequest(BaseModel):
    recipientEmail: str
    date: Optional[str] = ""

def gather_service_logs() -> List[Tuple[bytes, str]]:
    """
    Collect local service logs (fastapi.log, email_service.log) if they exist.
    """
    attachments = []
    logs_dir = os.path.join(os.getcwd(), "logs")
    candidates = ["fastapi.log", "email_service.log"]
    for fname in candidates:
        path = os.path.join(logs_dir, fname)
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    attachments.append((f.read(), fname))
            except Exception as e:
                logger.error(f"Failed to read {path}: {e}")
    return attachments

def log_to_pdf_bytes(title: str, subtitle: str, content: str) -> bytes:
    """
    Convert log content into PDF and return bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()

    heading_style = styles["Heading1"]
    heading_style.textColor = HexColor("#333")

    normal_style = styles["Normal"]
    normal_style.textColor = HexColor("#666")

    code_style = styles["Code"]
    code_style.fontSize = 10
    code_style.leading = 11
    code_style.backColor = HexColor("#f4f4f4")

    story = [
        Paragraph(title, heading_style),
        Paragraph(subtitle, normal_style),
        Spacer(1, 0.2 * inch),
        Preformatted(content, code_style)
    ]
    doc.build(story)

    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data

@app.get("/")
async def root():
    return {"message": "Divinely Bot Email Service is up."}

@app.post("/send-log-email")
async def send_log_email(request: LogRequest):
    if not request.logContent or request.logContent.strip() == "":
        raise HTTPException(status_code=400, detail="Empty log content received.")

    # Convert log content into PDF
    node_pdf_bytes = log_to_pdf_bytes(
        title="Node.js Logs",
        subtitle=f"File: {request.fileName}",
        content=request.logContent
    )

    attachments = [(node_pdf_bytes, f"nodejs-{request.fileName}.pdf")]

    # Add FastAPI/email_service logs from local logs folder
    service_attachments = gather_service_logs()
    if service_attachments:
        attachments.extend(service_attachments)

    subject = f"📄 Logs Received - {request.fileName}"
    plain_body = "Attached are the logs collected from Node.js and the email service."
    html_body = """
    <html>
      <body>
        <h2>Logs Received</h2>
        <p>The attached PDF files contain logs from:</p>
        <ul>
          <li><b>Node.js logger</b></li>
          <li><b>FastAPI service</b> (if available)</li>
        </ul>
      </body>
    </html>
    """

    success = send_email(
        request.recipientEmail,
        subject,
        plain_body,
        html_body,
        attachments=attachments
    )

    if success:
        return {"status": "success", "message": f"Logs (Node.js + service) sent as PDFs to {request.recipientEmail}"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send email")

@app.post("/send-no-logs-email")
async def send_no_logs(request: NoLogsEmailRequest):
    try:
        success = send_no_logs_email(receiver_email=request.recipientEmail, date=request.date)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to send no-logs email")
        return {"message": "No-logs email sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/send-notification-email")
async def send_notification(request: NotificationEmailRequest):
    try:
        success = send_notification_email(receiver_email=request.receiverEmail, message=request.message)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to send notification email")
        return {"message": "Notification email sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))