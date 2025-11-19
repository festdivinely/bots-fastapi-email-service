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

# Force load environment variables for both dev and production
def load_environment_variables():
    """Load environment variables with multiple fallback methods"""
    # Method 1: Try direct environment variables (Railway)
    email_sender = os.getenv("EMAIL_SENDER")
    email_password = os.getenv("EMAIL_PASSWORD")
    
    # Method 2: If not found, try .env file (Development)
    if not email_sender or not email_password:
        try:
            from dotenv import load_dotenv
            load_dotenv()
            email_sender = os.getenv("EMAIL_SENDER")
            email_password = os.getenv("EMAIL_PASSWORD")
            print("📁 Loaded from .env file (Development)")
        except ImportError:
            print("ℹ️ python-dotenv not available")
        except Exception as e:
            print(f"ℹ️ No .env file found: {e}")
    
    # Method 3: Debug - print all relevant environment variables
    print("=== ENVIRONMENT VARIABLES SCAN ===")
    all_vars = dict(os.environ)
    for key, value in all_vars.items():
        if any(term in key.upper() for term in ['EMAIL', 'SMTP', 'PASSWORD', 'USER']):
            masked_value = '*****' if 'PASSWORD' in key.upper() else value
            print(f"{key}: {masked_value}")
    
    return email_sender, email_password

# Load environment variables
EMAIL_SENDER, EMAIL_PASSWORD = load_environment_variables()

# Final debug output
print("=== FINAL CONFIGURATION ===")
print(f"EMAIL_SENDER: {EMAIL_SENDER}")
print(f"EMAIL_PASSWORD: {'*****' if EMAIL_PASSWORD else 'NOT SET'}")
print(f"Configuration Status: {'✅ READY' if EMAIL_SENDER and EMAIL_PASSWORD else '❌ NOT CONFIGURED'}")
print("===========================")

# Request models
class EmailRequest(BaseModel):
    type: str
    to: str
    data: Dict[str, Any]

# Add src directory to Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Email templates (import from separate files)
try:
    from src.email_templates.email_verification import email_verification_template
    from src.email_templates.device_verification import device_verification_template
    from src.email_templates.password_reset import password_reset_template
    print("✅ Email templates loaded successfully")
except ImportError as e:
    print(f"❌ Failed to load email templates: {e}")
    # Create fallback templates
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

        print(f"📧 Attempting to send email to: {to}")
        print(f"📧 Using sender: {EMAIL_SENDER}")

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
        print("🔗 Connecting to SMTP server...")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            print("🔐 Logging in...")
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            print("📤 Sending message...")
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
        "email_configured": bool(EMAIL_SENDER and EMAIL_PASSWORD),
        "endpoints": {
            "POST /api/send-email": "Send email notifications",
            "GET /debug": "Check environment configuration"
        }
    }

@app.get("/debug")
async def debug_env():
    """Debug endpoint to check environment configuration"""
    return {
        "email_configured": bool(EMAIL_SENDER and EMAIL_PASSWORD),
        "EMAIL_SENDER_set": bool(EMAIL_SENDER),
        "EMAIL_PASSWORD_set": bool(EMAIL_PASSWORD),
        "environment_variables": {
            k: ('*****' if 'PASSWORD' in k else v) 
            for k, v in os.environ.items() 
            if any(term in k for term in ['EMAIL', 'SMTP', 'RAILWAY'])
        }
    }

@app.post("/api/send-email")
async def send_email(request: EmailRequest):
    try:
        print(f"📨 Received email request: {request.type} to {request.to}")

        # Validate required fields
        if not request.type or not request.to or not request.data:
            raise HTTPException(
                status_code=400, 
                detail="Missing required fields: type, to, or data"
            )

        # Validate email configuration
        if not EMAIL_SENDER or not EMAIL_PASSWORD:
            error_msg = "Email service not configured - Environment variables missing"
            print(f"❌ {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)

        # Get email template
        email_content = get_email_template(request.type, request.data)
        print(f"📝 Using template: {request.type}")

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
            raise HTTPException(status_code=500, detail="Failed to send email")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Email service error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)