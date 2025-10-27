# app/routes/pharmacy_routes.py
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.db import db
from app.models.Pharmacy import Pharmacy
from app.models.prescriptions import Prescription
from app.models.users import User
from app.utils.role_required import role_required

pharmacy_bp = Blueprint("pharmacy_bp", __name__)

#View pharmacy profile
@pharmacy_bp.route("/pharmacies/<int:id>", methods=["GET"])
@jwt_required()
@role_required("pharmacy")
def get_pharmacy_profile(id):
    current_user_id = get_jwt_identity()
    pharmacy = Pharmacy.query.filter_by(user_id=current_user_id).first()

    if not pharmacy or pharmacy.id != id:
        return jsonify({"error": "Unauthorized or pharmacy not found"}), 403

    return jsonify({
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
    }), 200

# View prescriptions pending dispensing
@pharmacy_bp.route("/pharmacies/<int:id>/prescriptions", methods=["GET"])
@jwt_required()
@role_required("pharmacy")
def get_pharmacy_prescriptions(id):
    current_user_id = get_jwt_identity()
    pharmacy = Pharmacy.query.filter_by(user_id=current_user_id).first()

    if not pharmacy or pharmacy.id != id:
        return jsonify({"error": "Unauthorized or pharmacy not found"}), 403

    prescriptions = Prescription.query.filter_by(pharmacy_id=id).all()
    return jsonify([
        {
            "id": p.id,
            "doctor_id": p.doctor_id,
            "patient_id": p.patient_id,
            "medication_details": p.medication_details,
            "issued_date": p.issued_date.isoformat(),
        } for p in prescriptions
    ]), 200


#  PUT /pharmacies/<id>/verify-prescription/<prescription_id>
@pharmacy_bp.route("/pharmacies/<int:id>/verify-prescription/<int:prescription_id>", methods=["PUT"])
@jwt_required()
@role_required("pharmacy")
def verify_prescription(id, prescription_id):
    current_user_id = get_jwt_identity()
    pharmacy = Pharmacy.query.filter_by(user_id=current_user_id).first()

    if not pharmacy or pharmacy.id != id:
        return jsonify({"error": "Unauthorized or pharmacy not found"}), 403

    prescription = Prescription.query.get(prescription_id)
    if not prescription or prescription.pharmacy_id != id:
        return jsonify({"error": "Prescription not found or not assigned to this pharmacy"}), 404

    data = request.get_json()
    action = data.get("action", "").lower()

    if action not in ["verify", "dispense"]:
        return jsonify({"error": "Invalid action. Use 'verify' or 'dispense'."}), 400

    prescription.status = "verified" if action == "verify" else "dispensed"
    db.session.commit()

    return jsonify({"message": f"Prescription {action}d successfully"}), 200
