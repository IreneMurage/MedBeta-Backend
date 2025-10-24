from app.db import db

class Doctor(db.Model):
    __tablename__ = "doctors"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.id"))
    license_number = db.Column(db.String(100), unique=True, nullable=False)
    specialization = db.Column(db.String(100))
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

    user = db.relationship("User", back_populates="doctor")
    hospital = db.relationship("Hospital", back_populates="doctors")
    appointments = db.relationship("Appointment", back_populates="doctor")
    medical_records = db.relationship("MedicalRecord", back_populates="doctor")
    prescriptions = db.relationship("Prescription", back_populates="doctor")
    reviews = db.relationship("Review", back_populates="doctor")
    access_logs = db.relationship("AccessLog", back_populates="doctor")

def __repr__(self):
    return f"<Doctor {self.user.name} - {self.specialization}>"
