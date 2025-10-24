from app.db import db
from datetime import datetime, timezone
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

def utc_now():
    return datetime.now(timezone.utc)
# User model
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='patient')

    is_active = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(20), nullable=False, default='active')
    invite_token = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    # Relationships
    patient = db.relationship("Patient", uselist=False, back_populates="user")
    doctor = db.relationship("Doctor", uselist=False, back_populates="user")
    hospital = db.relationship("Hospital", uselist=False, back_populates="user")
    pharmacy = db.relationship("Pharmacy", uselist=False, back_populates="user")
    technician = db.relationship("Technician", back_populates="user", uselist=False)
    notifications = db.relationship("Notification", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
    
