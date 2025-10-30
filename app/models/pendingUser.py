from app.db import db
from datetime import datetime, timezone

def utc_now():
    return datetime.now(timezone.utc)
class PendingUser(db.Model):
    __tablename__ = "pending_users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='patient')
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.id"))
    invite_token = db.Column(db.String(255), unique=True, nullable=False)
    is_accepted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utc_now)
    expires_at = db.Column(db.DateTime)  

    hospital = db.relationship("Hospital", backref="pending_users")

    def __repr__(self):
        return f"<PendingUser {self.email} ({self.role})>"
