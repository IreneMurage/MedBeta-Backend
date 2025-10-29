from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity
from app.db import db
from app.models import Pharmacy, Prescription, User
from app.utils.role_required import role_required

pharmacy_bp = Blueprint("pharmacy_bp", __name__, url_prefix="/pharmacies")


# GET /pharmacies/profile
@pharmacy_bp.route("/profile", methods=["GET"])
@role_required("pharmacy")
def get_pharmacy_profile():
    user_id = int(get_jwt_identity())
    pharmacy = Pharmacy.query.filter_by(user_id=user_id).first()

    if not pharmacy:
        return jsonify({"error": "Pharmacy profile not found"}), 404

    return jsonify({
        "message": "Pharmacy profile retrieved successfully",
        "data": {
            "id": pharmacy.id,
            "name": pharmacy.name,
            "location": pharmacy.location,
            "license_number": pharmacy.license_number,
            "is_verified": pharmacy.is_verified,
            "user": {
                "id": pharmacy.user.id,
                "name": pharmacy.user.name,
                "email": pharmacy.user.email
            }
        }
    }), 200


# GET /pharmacies/prescriptions
@pharmacy_bp.route("/prescriptions", methods=["GET"])
@role_required("pharmacy")
def get_pharmacy_prescriptions():
    user_id = int(get_jwt_identity())
    pharmacy = Pharmacy.query.filter_by(user_id=user_id).first()

    if not pharmacy:
        return jsonify({"error": "Pharmacy profile not found"}), 404

    prescriptions = Prescription.query.filter_by(pharmacy_id=pharmacy.id).all()
    return jsonify({
        "message": "Prescriptions retrieved successfully",
        "data": [
            {
                "id": p.id,
                "doctor_id": p.doctor_id,
                "patient_id": p.patient_id,
                "medication_details": p.medication_details,
                "issued_date": p.issued_date.isoformat(),
                "status": p.status
            } for p in prescriptions
        ]
    }), 200


# PUT /pharmacies/prescriptions/<prescription_id>/action
@pharmacy_bp.route("/prescriptions/<int:prescription_id>/action", methods=["PUT"])
@role_required("pharmacy")
def verify_or_dispense_prescription(prescription_id):
    user_id = int(get_jwt_identity())
    pharmacy = Pharmacy.query.filter_by(user_id=user_id).first()

    if not pharmacy:
        return jsonify({"error": "Pharmacy profile not found"}), 404

    prescription = Prescription.query.get(prescription_id)
    if not prescription or prescription.pharmacy_id != pharmacy.id:
        return jsonify({"error": "Prescription not found or not assigned to this pharmacy"}), 404

    data = request.get_json() or {}
    action = data.get("action", "").lower()

    if action not in ["verify", "dispense"]:
        return jsonify({"error": "Invalid action. Use 'verify' or 'dispense'."}), 400

    # Optional: enforce logical order
    if action == "dispense" and prescription.status != "verified":
        return jsonify({"error": "Prescription must be verified before dispensing"}), 400

    prescription.status = "verified" if action == "verify" else "dispensed"
    db.session.commit()

    return jsonify({
        "message": f"Prescription successfully {prescription.status}.",
        "data": {
            "id": prescription.id,
            "status": prescription.status
        }
    }), 200
