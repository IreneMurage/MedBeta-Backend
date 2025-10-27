import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_email(to_email, subject, html_content):
    """
    Send an email using SendGrid. Falls back to console output if no API key is set.
    """
    sendgrid_api_key = os.getenv("SENDGRID_API_KEY")

    if not sendgrid_api_key:
        print("\n[DEV MODE] Email not sent (no SENDGRID_API_KEY).")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(f"Content:\n{html_content}\n")
        return

    try:
        message = Mail(
            from_email=os.getenv("FROM_EMAIL", "noreply@yourapp.com"),
            to_emails=to_email,
            subject=subject,
            html_content=html_content,
        )
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        print(f"Email sent to {to_email} — Status {response.status_code}")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")


def send_invite_email(to_email, token):
    """
    Sends an invitation email with a setup link.
    """
    setup_link = f"{os.getenv('FRONTEND_URL', 'http://localhost:5173')}/setup-password/{token}"
    subject = "You're invited to join MedBeta!"
    html_content = f"""
        <h2>Welcome to MediConnect 🎉</h2>
        <p>You’ve been invited to join our platform. Please click below to set your password and activate your account:</p>
        <p><a href="{setup_link}" target="_blank" style="color:#1a73e8;">Set up your account</a></p>
        <p>This link will expire in 7 days.</p>
    """
    send_email(to_email, subject, html_content)


def send_reset_email(to_email, token):
    """
    Sends a password reset email.
    """
    reset_link = f"{os.getenv('FRONTEND_URL', 'http://localhost:5173')}/reset-password/{token}"
    subject = "Password Reset Request "
    html_content = f"""
        <h2>Password Reset</h2>
        <p>We received a request to reset your password. Click the link below to create a new one:</p>
        <p><a href="{reset_link}" target="_blank" style="color:#1a73e8;">Reset Password</a></p>
        <p>If you didn’t request this, you can safely ignore this email.</p>
    """
    send_email(to_email, subject, html_content)
