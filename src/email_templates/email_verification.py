def email_verification_template(data: dict) -> dict:
    username = data.get("username", "")
    verification_link = data.get("verificationLink", "")
    token = data.get("token", "")
    support_email = data.get("supportEmail", "support@quantumrobots.com")
    
    subject = "Verify Your Email - Quantum Robots"
    
    text = f"""
Welcome to Quantum Robots

To verify your email, use the following token:

Token: {token}

Or click this link to verify: {verification_link}

This token expires in 15 minutes. If you didn't register, ignore this email.

Need help? Contact {support_email}
    """
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Your Email - Quantum Robots</title>
</head>
<body style="margin:0; padding:0; font-family: Arial, sans-serif; background-color:#f4f7fb;">
  <table width="100%" border="0" cellspacing="0" cellpadding="0" style="padding:20px 0;">
    <tr>
      <td align="center">
        <table width="600" border="0" cellspacing="0" cellpadding="0" style="background:#ffffff; border-radius:12px; box-shadow:0 4px 12px rgba(0,0,0,0.1); overflow:hidden;">
          <tr>
            <td align="center" style="background: #000000; padding:30px; color:#00ff41; font-size:24px; font-weight:bold;">
              QUANTUM ROBOTS
            </td>
          </tr>
          <tr>
            <td style="padding:30px; color:#333333; font-size:16px; line-height:1.6;">
              <h2 style="margin-top:0; color:#000000;">Welcome, {username}!</h2>
              <p>To verify your email, use the token below:</p>
              <p style="text-align:center; margin:30px 0;">
                <span style="font-size:18px; background:#f0f0f0; padding:15px 25px; border-radius:8px; display:inline-block; font-weight:bold; border: 2px solid #00ff41;">
                  {token}
                </span>
              </p>
              <p style="text-align:center;">
                <a href="{verification_link}" style="background:#00ff41; color:#000000; padding:12px 30px; text-decoration:none; border-radius:5px; font-weight:bold; display:inline-block;">
                  Verify Email
                </a>
              </p>
              <p>This token expires in <b>15 minutes</b>. If you didn't sign up, ignore this email.</p>
            </td>
          </tr>
          <tr>
            <td align="center" style="background:#000000; color:#00ff41; padding:20px; font-size:13px;">
              &copy; {data.get('year', '2024')} Quantum Robots. All rights reserved.<br/>
              Need help? <a href="mailto:{support_email}" style="color:#00ff41; text-decoration:none;">Contact Support</a>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
    """
    
    return {
        "subject": subject,
        "text": text.strip(),
        "html": html
    }