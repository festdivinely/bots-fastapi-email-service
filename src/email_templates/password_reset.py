def password_reset_template(data: dict) -> dict:
    username = data.get("username", "")
    reset_link = data.get("resetLink", "")
    token = data.get("token", "")
    support_email = data.get("supportEmail", "support@quantumrobots.com")
    
    subject = "Reset Your Password - Quantum Robots"
    
    text = f"""
Password Reset Request - Quantum Robots

Hello {username},

We received a request to reset your password for your Quantum Robots account.

Reset Token: {token}

Reset Link: {reset_link}

This password reset link will expire in 1 hour.

If you didn't request a password reset, please ignore this email.

Need help? Contact {support_email}
    """
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Password Reset - Quantum Robots</title>
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
              <h2 style="margin-top:0; color:#000000;">Password Reset Request</h2>
              <p>Hello {username},</p>
              <p>We received a request to reset your password for your Quantum Robots account.</p>
              <p><strong>Reset Token:</strong></p>
              <div style="background:#f0f0f0; padding:10px; border-radius:5px; font-family:monospace; margin:10px 0;">
                {token}
              </div>
              <p style="text-align:center; margin:30px 0;">
                <a href="{reset_link}" style="background:#00ff41; color:#000000; padding:12px 30px; text-decoration:none; border-radius:5px; font-weight:bold; display:inline-block;">
                  Reset Password
                </a>
              </p>
              <p>If the button doesn't work, copy and paste this link in your browser:</p>
              <p style="word-break:break-all;">{reset_link}</p>
              <p><strong>This password reset link will expire in 1 hour.</strong></p>
              <p>If you didn't request a password reset, please ignore this email.</p>
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