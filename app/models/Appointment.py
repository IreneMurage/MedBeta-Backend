from datetime import datetime, timezone
from app.db import db

def utc_now():
    return datetime.now(timezone.utc)

class Appointment(db.Model):
    __tablename__ = "appointments"
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    status = db.Column(db.Enum("pending", "accepted", "declined", "completed", name="appointment_status"), default="pending")
    created_at = db.Column(db.DateTime, default=utc_now)

    patient = db.relationship("Patient", back_populates="appointments")
    doctor = db.relationship("Doctor", back_populates="appointments")
    hospital = db.relationship("Hospital", back_populates="appointments")
    medical_record = db.relationship("MedicalRecord", back_populates="appointment", uselist=False)


    def __repr__(self):
        return f"<Appointment {self.date} - {self.status}>"