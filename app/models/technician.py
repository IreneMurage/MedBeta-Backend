from datetime import datetime, timezone
from app.db import db

def utc_now():
    return datetime.now(timezone.utc)

class Technician(db.Model):
    __tablename__ = "technicians"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    profile_pic = db.Column(db.String(255))
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime, default=utc_now)

    # Relationships
    user = db.relationship("User", back_populates="technician")
    test_requests = db.relationship("TestRequest", back_populates="technician")

    def __repr__(self):
        return f"<Technician {self.user.name}>"



class TestRequest(db.Model):
    __tablename__ = "test_requests"

    id = db.Column(db.Integer, primary_key=True)
    test_name = db.Column(db.String(150), nullable=False)
    status = db.Column(db.String(20), default="Pending") 
    date_requested = db.Column(db.DateTime, default=utc_now)
    date_completed = db.Column(db.DateTime, nullable=True)
    results = db.Column(db.Text, nullable=True)


    # Foreign keys
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    technician_id = db.Column(db.Integer, db.ForeignKey("technicians.id"), nullable=True)

    # Relationships
    doctor = db.relationship("Doctor", backref="test_requests")
    patient = db.relationship("Patient", backref="test_requests")
    technician = db.relationship("Technician", back_populates="test_requests")

    def __repr__(self):
        return f"<TestRequest {self.test_name} - {self.status}>"
