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

# Environment detection
def load_environment():
    """Load environment variables for both development and production"""
    # Check if we're in development (local) or production (Railway)
    is_development = os.getenv("RAILWAY_ENVIRONMENT") is None and os.getenv("RAILWAY") is None
    
    if is_development:
        # Development: Use python-dotenv to load from .env file
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print("🔧 Development environment: Loading from .env file")
        except ImportError:
            print("❌ python-dotenv not installed. Run: pip install python-dotenv")
    else:
        # Production: Railway environment variables are automatically available
        print("🚀 Production environment: Using Railway environment variables")
    
    return is_development

# Load environment based on current context
IS_DEVELOPMENT = load_environment()

# Email configuration
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Debug: Check environment variables
print("=== ENVIRONMENT CONFIGURATION ===")
print(f"Environment: {'Development' if IS_DEVELOPMENT else 'Production'}")
print(f"EMAIL_SENDER: {EMAIL_SENDER}")
print(f"EMAIL_PASSWORD: {'*' * len(EMAIL_PASSWORD) if EMAIL_PASSWORD else 'NOT SET'}")
print("==================================")

if not EMAIL_SENDER or not EMAIL_PASSWORD:
    print("❌ CRITICAL: Email environment variables not configured!")
else:
    print("✅ Email environment variables loaded successfully")

# Request models
class EmailRequest(BaseModel):
    type: str
    to: str
    data: Dict[str, Any]

# Add src directory to Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Email templates (import from separate files)
from src.email_templates.email_verification import email_verification_template
from src.email_templates.device_verification import device_verification_template
from src.email_templates.password_reset import password_reset_template

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
        "environment": "development" if IS_DEVELOPMENT else "production",
        "endpoints": {
            "POST /api/send-email": "Send email notifications",
            "GET /debug-env": "Check environment configuration"
        },
        "usage": {
            "email_verification": "Send email verification during signup",
            "device_verification": "Send device verification code for new devices", 
            "password_reset": "Send password reset emails"
        }
    }

@app.get("/debug-env")
async def debug_env():
    """Debug endpoint to check environment configuration"""
    return {
        "environment": "development" if IS_DEVELOPMENT else "production",
        "EMAIL_SENDER": "✅ Set" if EMAIL_SENDER else "❌ Not set",
        "EMAIL_PASSWORD": "✅ Set" if EMAIL_PASSWORD else "❌ Not set",
        "service_status": "Configured" if EMAIL_SENDER and EMAIL_PASSWORD else "Not Configured",
        "railway_environment": os.getenv("RAILWAY_ENVIRONMENT"),
        "railway_service": os.getenv("RAILWAY_SERVICE_NAME")
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
                detail="Email service not configured - check environment variables"
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
                "message": "Email sent successfully",
                "environment": "development" if IS_DEVELOPMENT else "production"
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