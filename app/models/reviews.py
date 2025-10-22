from app.db import db
from datetime import datetime, timezone


def utc_now():
    return datetime.now(timezone.utc)


class Review(db.Model):
    tablename = "reviews"

id = db.Column(db.Integer, primary_key=True)
patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"))
hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.id"))
rating = db.Column(db.Integer, nullable=False)
comment = db.Column(db.Text)
created_at = db.Column(db.DateTime, default=utc_now)

patient = db.relationship("Patient", back_populates="reviews")
doctor = db.relationship("Doctor", back_populates="reviews")
hospital = db.relationship("Hospital", back_populates="reviews")

def __repr__(self):
    return f"<Review {self.rating} stars>"


