from app.db import db

class Hospital(db.Model):
    __tablename__ = "hospitals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(255))
    license_number = db.Column(db.String(100), unique=True)
    is_verified = db.Column(db.Boolean, default=False)

    user = db.relationship("User", back_populates="hospital")
    doctors = db.relationship("Doctor", back_populates="hospital")
    appointments = db.relationship("Appointment", back_populates="hospital")
    reviews = db.relationship("Review", back_populates="hospital")

def __repr__(self):
    return f"<Hospital {self.name}>"