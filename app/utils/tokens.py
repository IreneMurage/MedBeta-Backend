import jwt
from datetime import datetime, timedelta
from flask import current_app

def generate_token(email, expires_in=3600):
    """Generate a JWT token for password reset or invitations."""
    payload = {
        "email": email,
        "exp": datetime.utcnow() + timedelta(seconds=expires_in)
    }
    secret = current_app.config["SECRET_KEY"]
    return jwt.encode(payload, secret, algorithm="HS256")

def verify_token(token):
    """Verify the JWT token and return the email if valid."""
    secret = current_app.config["SECRET_KEY"]
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload["email"]
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
