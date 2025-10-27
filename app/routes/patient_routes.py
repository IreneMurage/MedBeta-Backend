# app/routes/patient_routes.py
from flask import Blueprint, jsonify, request
from app.models.patient import Patient
from app.db import db
import logging

patient_bp = Blueprint("patient", __name__, url_prefix="/patients")

# GET patient profile
@patient_bp.route("/<int:id>", methods=["GET"])
def get_patient_profile(id):
    try:
        patient = Patient.query.get(id)
        if not patient:
            return jsonify({"error": "Patient not found"}), 404
        return jsonify({
            "id": patient.id,
            "name": patient.name,
            "email": patient.email,
            "phone": patient.phone,
            "address": patient.address
        }), 200
    except Exception as e:
        logging.error(f"Error getting patient profile: {e}")
        return jsonify({"error": "Internal server error"}), 500


# PUT update profile
@patient_bp.route("/<int:id>", methods=["PUT"])
def update_patient_profile(id):
    data = request.get_json()
    patient = Patient.query.get(id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    allowed_fields = ["name", "email", "phone", "address", "dob"]
    for field in allowed_fields:
        if field in data:
            setattr(patient, field, data[field])

    try:
        db.session.commit()
        return jsonify({"message": "Profile updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating profile: {e}")
        return jsonify({"error": "Failed to update profile"}), 500
