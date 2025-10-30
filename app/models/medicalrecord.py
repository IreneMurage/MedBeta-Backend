from app.db import db
from datetime import datetime, timezone
from app.utils.encryption import encrypt_text, decrypt_text

def utc_now():
    return datetime.now(timezone.utc)

# Medical Record model
class MedicalRecord(db.Model):
    __tablename__ = "medical_records"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey("appointments.id"), nullable=True)
    diagnosis = db.Column(db.Text, nullable=True)
    treatment = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    # relationships
    patient = db.relationship("Patient", back_populates="medical_records")
    doctor = db.relationship("Doctor", back_populates="medical_records")
    appointment = db.relationship("Appointment", back_populates="medical_record", uselist=False)

    # @property
    # def diagnosis(self):
    #     return decrypt_text(self._diagnosis)

    # @diagnosis.setter
    # def diagnosis(self, value):
    #     self._diagnosis = encrypt_text(value)

    # @property
    # def treatment(self):
    #     return decrypt_text(self._treatment)

    # @treatment.setter
    # def treatment(self, value):
    #     self._treatment = encrypt_text(value)

    # @property
    # def notes(self):
    #     return decrypt_text(self._notes)

    # @notes.setter
    # def notes(self, value):
    #     self._notes = encrypt_text(value)

