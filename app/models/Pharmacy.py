from datetime import datetime, timezone
from app.db import db

def utc_now():
    return datetime.now(timezone.utc)

class Pharmacy(db.Model):
    __tablename__ = "pharmacies"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.id"), nullable=True)  

    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(255))
    license_number = db.Column(db.String(100), unique=True)
    is_verified = db.Column(db.Boolean, default=False)

    user = db.relationship("User", back_populates="pharmacy")
    prescriptions = db.relationship("Prescription", back_populates="pharmacy")
    hospital = db.relationship("Hospital", back_populates="pharmacies")  


    def __repr__(self):
        return f"<Pharmacy {self.name}>"