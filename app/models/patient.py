from app.db import db
from datetime import datetime, timezone
# Patient model
class Patient(db.Model):
    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    phone = db.Column(db.String(20))
    medical_history = db.Column(db.Text)

    user = db.relationship("User", back_populates="patient")
    medical_records = db.relationship("MedicalRecord", back_populates="patient")
    # add to doctor model - medical_records = db.relationship("MedicalRecord", back_populates="doctor")
    appointments = db.relationship("Appointment", back_populates="patient")
    prescriptions = db.relationship("Prescription", back_populates="patient")
    reviews = db.relationship("Review", back_populates="patient")
    access_logs = db.relationship("AccessLog", back_populates="patient")

    def __repr__(self):
        return f"<Patient {self.user.name}>"
