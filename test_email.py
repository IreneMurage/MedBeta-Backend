import os
from app.utils.email_utils import send_email
from dotenv import load_dotenv

# Load your .env so it knows your Brevo key
load_dotenv()
# print("CWD:", os.getcwd())
# print("BREVO_API_KEY:", os.getenv("BREVO_API_KEY"))

to_email = "muthonimurage361@gmail.com"

subject = "MedBeta Email Test"
html_content = """
    <h2>Hello from MedBeta </h2>
    <p>This is a test email sent via <b>Brevo API</b>.</p>
    <p>If you received this, your integration works perfectly </p>
"""

send_email(to_email, subject, html_content)
print("Test email function executed.")