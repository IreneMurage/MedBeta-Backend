# app/routes/patient_routes.py
"""Patient routes for MedBeta backend API."""
from flask import Blueprint, jsonify, request
from app.models.patient import Patient
from app.models.Appointment import Appointment
from app.models.prescriptions import Prescription
from app.models.reviews import Review
from app.models.medicalrecord import MedicalRecord
from app.db import db
from datetime import datetime
import logging

patient_bp = Blueprint("patient", __name__, url_prefix="/patients")

# -------------------------------
# GET: View patient profile
# -------------------------------
@patient_bp.route("/<int:id>", methods=["GET"])
def get_patient_profile(id):
    try:
        patient = Patient.query.get(id)
        if not patient:
            return jsonify({"error": "Patient not found"}), 404
        return jsonify({"id": patient.id, "phone": patient.phone, "address": patient.address}), 200
    except Exception as e:
        logging.error(f"Error getting patient profile: {e}")
        return jsonify({"error": "Internal server error"}), 500


# -------------------------------
# PUT: Update patient profile
# -------------------------------
@patient_bp.route("/<int:id>", methods=["PUT"])
def update_patient_profile(id):
    patient = Patient.query.get(id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    data = request.get_json()
    allowed_fields = ["name", "email", "phone", "address", "dob"]
    for field in allowed_fields:
        if field in data:
            setattr(patient, field, data[field])

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating patient profile: {e}")
        return jsonify({"error": "Failed to update profile"}), 500
    return jsonify({"message": "Profile updated successfully"}), 200


# -------------------------------
# GET: View all medical records
# -------------------------------
@patient_bp.route("/<int:id>/medical-records", methods=["GET"])
def get_medical_records(id):
    try:
        records = MedicalRecord.query.filter_by(patient_id=id).all()
        if not records:
            return jsonify({"message": "No medical records found"}), 404
        return jsonify([{"id": r.id, "diagnosis": r.diagnosis, "treatment": r.treatment} for r in records]), 200
    except Exception as e:
        logging.error(f"Error getting medical records: {e}")
        return jsonify({"error": "Internal server error"}), 500


# -------------------------------
# POST: Book new appointment
# -------------------------------
@patient_bp.route("/<int:id>/appointments", methods=["POST"])
def book_appointment(id):
    data = request.get_json()

    # ✅ Check required fields
    required_fields = ["doctor_id", "hospital_id", "date", "time"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    try:
        # ✅ Parse date & time safely
        appointment_date = datetime.strptime(data["date"], "%Y-%m-%d").date()
        appointment_time = datetime.strptime(data["time"], "%H:%M").time()

        # ✅ Create new Appointment
        new_appointment = Appointment(
            patient_id=id,
            doctor_id=data["doctor_id"],
            hospital_id=data["hospital_id"],
            date=appointment_date,
            time=appointment_time,
            status="pending"
        )

        db.session.add(new_appointment)
        db.session.commit()

        return jsonify({
            "message": "Appointment booked successfully",
            "appointment": {
                "id": new_appointment.id,
                "doctor_id": new_appointment.doctor_id,
                "hospital_id": new_appointment.hospital_id,
                "date": new_appointment.date.isoformat(),
                "time": new_appointment.time.strftime("%H:%M"),
                "status": new_appointment.status
            }
        }), 201

    except ValueError:
        return jsonify({"error": "Invalid date or time format. Expected 'YYYY-MM-DD' and 'HH:MM'"}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# -------------------------------
# GET: All appointments for patient
# -------------------------------
@patient_bp.route("/<int:id>/appointments", methods=["GET"])
def get_appointments(id):
    try:
        appointments = Appointment.query.filter_by(patient_id=id).all()
        if not appointments:
            return jsonify({"message": "No appointments found"}), 404
        return jsonify([{"id": a.id, "date": str(a.date), "time": str(a.time), "status": a.status} for a in appointments]), 200
    except Exception as e:
        logging.error(f"Error getting appointments: {e}")
        return jsonify({"error": "Internal server error"}), 500


# -------------------------------
# POST: Add review for doctor or hospital
# -------------------------------
@patient_bp.route("/<int:id>/reviews", methods=["POST"])
def add_review(id):
    data = request.get_json()

    # ✅ Validate required fields
    if not data:
        return jsonify({"error": "Request body cannot be empty"}), 400

    if "rating" not in data:
        return jsonify({"error": "Missing required field: rating"}), 400

    # ✅ Ensure at least one target (doctor or hospital) is provided
    if not data.get("doctor_id") and not data.get("hospital_id"):
        return jsonify({"error": "Either 'doctor_id' or 'hospital_id' must be provided"}), 400

    # ✅ Create the review safely
    try:
        new_review = Review(
            patient_id=id,
            doctor_id=data.get("doctor_id"),
            hospital_id=data.get("hospital_id"),
            rating=data["rating"],
            comment=data.get("comment", "")
        )

        db.session.add(new_review)
        db.session.commit()

        return jsonify({
            "message": "Review added successfully",
            "review": {
                "id": new_review.id,
                "patient_id": new_review.patient_id,
                "doctor_id": new_review.doctor_id,
                "hospital_id": new_review.hospital_id,
                "rating": new_review.rating,
                "comment": new_review.comment,
                "created_at": new_review.created_at.isoformat()
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500



# -------------------------------
# GET: View prescriptions linked to patient
# -------------------------------
@patient_bp.route("/<int:id>/prescriptions", methods=["GET"])
def get_prescriptions(id):
    try:
        prescriptions = Prescription.query.filter_by(patient_id=id).all()
        if not prescriptions:
            return jsonify({"message": "No prescriptions found"}), 404
        return jsonify([{"id": p.id, "medication_details": p.medication_details, "issued_date": str(p.issued_date)} for p in prescriptions]), 200
    except Exception as e:
        logging.error(f"Error getting prescriptions: {e}")
        return jsonify({"error": "Internal server error"}), 500
