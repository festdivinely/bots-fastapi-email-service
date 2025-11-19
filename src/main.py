import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="Quantum Robots Email Service")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Email configuration
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Request models
class EmailRequest(BaseModel):
    type: str
    to: str
    data: Dict[str, Any]

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


# Email templates (import from separate files)
# Use absolute imports
from .email_templates.email_verification import email_verification_template
from .email_templates.device_verification import device_verification_template
from .email_templates.password_reset import password_reset_template

def get_email_template(email_type: str, data: Dict[str, Any]) -> Dict[str, str]:
    """Get the appropriate email template based on type"""
    if email_type == "email_verification":
        return email_verification_template(data)
    elif email_type == "device_verification":
        return device_verification_template(data)
    elif email_type == "password_reset":
        return password_reset_template(data)
    else:
        raise ValueError(f"Unknown email type: {email_type}")

def send_email_via_smtp(to: str, subject: str, text_content: str, html_content: str) -> bool:
    """Send email using SMTP"""
    try:
        if not EMAIL_SENDER or not EMAIL_PASSWORD:
            print("❌ Email credentials not configured")
            return False

        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_SENDER
        msg['To'] = to

        # Attach both text and HTML versions
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        msg.attach(part1)
        msg.attach(part2)

        # Send email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)

        print(f"✅ Email sent successfully to {to}")
        return True

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

@app.get("/")
async def root():
    return {
        "success": True,
        "message": "Quantum Robots Email Service is running",
        "endpoints": {
            "POST /api/send-email": "Send email notifications"
        },
        "usage": {
            "email_verification": "Send email verification during signup",
            "device_verification": "Send device verification code for new devices", 
            "password_reset": "Send password reset emails"
        }
    }

@app.post("/api/send-email")
async def send_email(request: EmailRequest):
    try:
        # Validate required fields
        if not request.type or not request.to or not request.data:
            raise HTTPException(
                status_code=400, 
                detail="Missing required fields: type, to, or data"
            )

        # Validate email configuration
        if not EMAIL_SENDER or not EMAIL_PASSWORD:
            raise HTTPException(
                status_code=500,
                detail="Email service not configured"
            )

        # Get email template
        email_content = get_email_template(request.type, request.data)

        # Send email
        success = send_email_via_smtp(
            to=request.to,
            subject=email_content["subject"],
            text_content=email_content["text"],
            html_content=email_content["html"]
        )

        if success:
            return {
                "success": True,
                "message": "Email sent successfully"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to send email"
            )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"❌ Email service error: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e) or "Failed to send email"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)