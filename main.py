import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI(title="Quantum Robots Email Service")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HARDCODE FOR TESTING - Remove this after testing!
EMAIL_SENDER = "festusheav@gmail.com"
EMAIL_PASSWORD = "owfyuvmjsjeiydry"

print("=== FORCED CONFIGURATION ===")
print(f"EMAIL_SENDER: {EMAIL_SENDER}")
print(f"EMAIL_PASSWORD: *****")
print("✅ USING HARDCODED CREDENTIALS FOR TESTING")
print("===========================")

# Request models
class EmailRequest(BaseModel):
    type: str
    to: str
    data: Dict[str, Any]

# Email templates (fallback versions)
def email_verification_template(data):
    return {
        "subject": "Verify Your Email",
        "text": f"Your verification code is: {data.get('code', 'N/A')}",
        "html": f"<h1>Your verification code is: {data.get('code', 'N/A')}</h1>"
    }

def device_verification_template(data):
    return {
        "subject": "New Device Verification",
        "text": f"Verification code: {data.get('code', 'N/A')} for device: {data.get('device_name', 'Unknown')}",
        "html": f"<h1>Device Verification</h1><p>Code: {data.get('code', 'N/A')}</p><p>Device: {data.get('device_name', 'Unknown')}</p>"
    }

def password_reset_template(data):
    return {
        "subject": "Password Reset",
        "text": f"Reset your password using this link: {data.get('reset_link', 'N/A')}",
        "html": f"<h1>Password Reset</h1><p><a href='{data.get('reset_link', '#')}'>Click here to reset your password</a></p>"
    }

def get_email_template(email_type: str, data: Dict[str, Any]) -> Dict[str, str]:
    if email_type == "email_verification":
        return email_verification_template(data)
    elif email_type == "device_verification":
        return device_verification_template(data)
    elif email_type == "password_reset":
        return password_reset_template(data)
    else:
        raise ValueError(f"Unknown email type: {email_type}")

def send_email_via_smtp(to: str, subject: str, text_content: str, html_content: str) -> bool:
    try:
        print(f"📧 Attempting to send email to: {to}")

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
        print(f"❌ Failed to send email: {str(e)}")
        return False

@app.get("/")
async def root():
    return {
        "success": True,
        "message": "Quantum Robots Email Service is running",
        "status": "HARDCODED_CREDENTIALS",
        "endpoints": {
            "POST /api/send-email": "Send email notifications",
            "GET /debug": "Check environment configuration"
        }
    }

@app.get("/debug")
async def debug_env():
    return {
        "status": "using_hardcoded_credentials",
        "email_sender_set": True,
        "email_password_set": True,
        "message": "Testing with hardcoded credentials"
    }

@app.post("/api/send-email")
async def send_email(request: EmailRequest):
    try:
        print(f"📨 Received email request: {request.type} to {request.to}")

        if not request.type or not request.to or not request.data:
            raise HTTPException(status_code=400, detail="Missing required fields")

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
            return {"success": True, "message": "Email sent successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send email")

    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)