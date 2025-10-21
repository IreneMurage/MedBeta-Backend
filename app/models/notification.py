from app.db import db
from datetime import datetime, timezone

def utc_now():
    return datetime.now(timezone.utc)
# Notification model
class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=utc_now)

    user = db.relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification to {self.user.email}>"