from app.db import db
from datetime import datetime, timezone

def utc_now():
    return datetime.now(timezone.utc)

class Prescription(db.Model):
    __tablename__ = "prescriptions"

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    pharmacy_id = db.Column(db.Integer, db.ForeignKey("pharmacies.id"))
    medication_details = db.Column(db.Text, nullable=False)
    issued_date = db.Column(db.DateTime, default=utc_now)

    doctor = db.relationship("Doctor", back_populates="prescriptions")
    patient = db.relationship("Patient", back_populates="prescriptions")
    pharmacy = db.relationship("Pharmacy", back_populates="prescriptions")

    def __repr__(self):
        return f"<Prescription {self.id}>"