"""Secure Patient routes for MedBeta backend API."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity
from datetime import datetime
import logging

from app.models.patient import Patient
from app.models.Appointment import Appointment
from app.models.reviews import Review
from app.models.medicalrecord import MedicalRecord
from app.models.prescriptions import Prescription 
from app.db import db
from app.utils.role_required import role_required

patient_bp = Blueprint("patient_bp", __name__, url_prefix="/patients")


# -------------------------------------------------
# Helper: Get logged-in patient safely from JWT
# -------------------------------------------------
def get_current_patient():
    identity = get_jwt_identity()

    # handle both raw id or dict identity
    if isinstance(identity, dict):
        user_id = identity.get("id")
    else:
        user_id = int(identity)

    patient = Patient.query.filter_by(user_id=user_id).first()
    if not patient:
        return None, jsonify({"error": "Patient not found"}), 404
    return patient, None, None


# -------------------------------------------------
# GET: View patient profile
# -------------------------------------------------
@patient_bp.route("/profile", methods=["GET"])
@role_required("patient")
def get_patient_profile():
    """Retrieve logged-in patient's profile."""
    patient, err, code = get_current_patient()
    if err:
        return err, code

    return jsonify({
        "id": patient.id,
        "phone": patient.phone,
        "address": patient.address,
        "dob": str(patient.dob) if patient.dob else None
    }), 200


# -------------------------------------------------
# PUT: Update patient profile
# -------------------------------------------------
@patient_bp.route("/profile", methods=["PUT"])
@role_required("patient")
def update_patient_profile():
    """Allow a patient to update their profile details."""
    patient, err, code = get_current_patient()
    if err:
        return err, code

    data = request.get_json() or {}
    allowed_fields = ["phone", "address", "dob"]

    for field in allowed_fields:
        if field in data:
            setattr(patient, field, data[field])

    try:
        db.session.commit()
        return jsonify({"message": "Profile updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating patient profile: {e}")
        return jsonify({"error": "Failed to update profile"}), 500


# -------------------------------------------------
# GET: All medical records
# -------------------------------------------------
@patient_bp.route("/medical-records", methods=["GET"])
@role_required("patient")
def get_medical_records():
    """Retrieve all medical records for logged-in patient."""
    patient, err, code = get_current_patient()
    if err:
        return err, code

    records = MedicalRecord.query.filter_by(patient_id=patient.id).all()
    if not records:
        return jsonify({"message": "No medical records found"}), 404

    return jsonify([
        {"id": r.id, "diagnosis": r.diagnosis, "treatment": r.treatment}
        for r in records
    ]), 200


# -------------------------------------------------
# POST: Book a new appointment
# -------------------------------------------------
@patient_bp.route("/appointments", methods=["POST"])
@role_required("patient")
def book_appointment():
    """Book a new appointment with a doctor."""
    patient, err, code = get_current_patient()
    if err:
        return err, code

    data = request.get_json() or {}
    required_fields = ["doctor_id", "hospital_id", "date", "time"]

    missing = [f for f in required_fields if f not in data]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    try:
        appointment_date = datetime.strptime(data["date"], "%Y-%m-%d").date()
        appointment_time = datetime.strptime(data["time"], "%H:%M").time()

        new_appointment = Appointment(
            patient_id=patient.id,
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
        return jsonify({
            "error": "Invalid date or time format. Expected 'YYYY-MM-DD' and 'HH:MM'"
        }), 400
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error booking appointment: {e}")
        return jsonify({"error": "Failed to book appointment"}), 500


# -------------------------------------------------
# GET: All appointments for logged-in patient
# -------------------------------------------------
@patient_bp.route("/appointments", methods=["GET"])
@role_required("patient")
def get_appointments():
    """Retrieve all appointments for the logged-in patient."""
    patient, err, code = get_current_patient()
    if err:
        return err, code

    appointments = Appointment.query.filter_by(patient_id=patient.id).all()
    if not appointments:
        return jsonify({"message": "No appointments found"}), 404

    return jsonify([
        {"id": a.id, "date": str(a.date), "time": str(a.time), "status": a.status}
        for a in appointments
    ]), 200


# -------------------------------------------------
# POST: Add review for doctor or hospital
# -------------------------------------------------
@patient_bp.route("/reviews", methods=["POST"])
@role_required("patient")
def add_review():
    """Submit a review for a doctor or hospital."""
    patient, err, code = get_current_patient()
    if err:
        return err, code

    data = request.get_json() or {}

    if "rating" not in data:
        return jsonify({"error": "Missing required field: rating"}), 400
    if not data.get("doctor_id") and not data.get("hospital_id"):
        return jsonify({"error": "Either 'doctor_id' or 'hospital_id' must be provided"}), 400

    try:
        new_review = Review(
            patient_id=patient.id,
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
                "rating": new_review.rating,
                "comment": new_review.comment,
                "created_at": new_review.created_at.isoformat()
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error adding review: {e}")
        return jsonify({"error": "Failed to add review"}), 500


# -------------------------------------------------
# GET: View prescriptions linked to patient
# -------------------------------------------------
@patient_bp.route("/prescriptions", methods=["GET"])
@role_required("patient")  # ✅ Added missing decorator
def get_prescriptions():
    """Retrieve all prescriptions for the logged-in patient."""
    patient, err, code = get_current_patient()
    if err:
        return err, code

    prescriptions = Prescription.query.filter_by(patient_id=patient.id).all()
    if not prescriptions:
        return jsonify({"message": "No prescriptions found"}), 404

    return jsonify([
        {
            "id": p.id,
            "medication_details": p.medication_details,
            "issued_date": str(p.issued_date)
        } for p in prescriptions
    ]), 200
