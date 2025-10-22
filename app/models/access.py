from app.db import db
from datetime import datetime, timezone

def utc_now():
    return datetime.now(timezone.utc)



class AccessLog(db.Model):
    __tablename__ = "access_logs"

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"))
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"))
    accessed_at = db.Column(db.DateTime, default=utc_now)
    purpose = db.Column(db.String(255))  # e.g., "viewed record", "updated prescription"

    doctor = db.relationship("Doctor", back_populates="access_logs")
    patient = db.relationship("Patient", back_populates="access_logs")

    def __repr__(self):
        return f"<AccessLog Doctor:{self.doctor_id} Patient:{self.patient_id}>"