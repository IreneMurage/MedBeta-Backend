"""Access Logs (Audit) routes for MedBeta backend API — by Horace."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timezone
from app.db import db
from app.models.access import AccessLog
from app.models.users import User
from app.models.patient import Patient
from app.utils.role_required import role_required
import logging

audit_bp = Blueprint("audit_bp", __name__, url_prefix="/access-logs")

# ✅ POST /access-logs
# Auto-created when doctor accesses a patient's record (system-generated)
@audit_bp.route("/", methods=["POST"])
@jwt_required()
@role_required("doctor")
def create_access_log():
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}

        patient_id = data.get("patient_id")
        action = data.get("action", "viewed record")

        if not patient_id:
            return jsonify({"error": "patient_id is required"}), 400

        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({"error": "Patient not found"}), 404

        new_log = AccessLog(
            user_id=user_id,
            patient_id=patient_id,
            purpose=action,
            accessed_at=datetime.now(timezone.utc)
        )

        db.session.add(new_log)
        db.session.commit()

        return jsonify({
            "message": "Access log recorded successfully",
            "log": {
                "id": new_log.id,
                "user_id": new_log.user_id,
                "patient_id": new_log.patient_id,
                "action": new_log.purpose,
                "timestamp": new_log.accessed_at.isoformat()
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        logging.error("Error creating access log: %s", e)
        return jsonify({"error": "Failed to record access log"}), 500


# ✅ GET /access-logs — Admin-only view of all patient record access
@audit_bp.route("/", methods=["GET"])
@jwt_required()
@role_required("admin")
def get_all_access_logs():
    try:
        logs = AccessLog.query.order_by(AccessLog.accessed_at.desc()).all()

        return jsonify([
            {
                "id": log.id,
                "user_id": log.user_id,
                "user_name": getattr(log.user, "username", None),
                "patient_id": log.patient_id,
                "patient_name": getattr(log.patient, "full_name", None),
                "action": log.action,
                "timestamp": log.access_time.isoformat()
            }
            for log in logs
        ]), 200

    except Exception as e:
        logging.error("Error fetching access logs: %s", e)
        return jsonify({"error": "Failed to fetch logs"}), 500


# ✅ GET /access-logs/patient/<patient_id>
# View who accessed a specific patient’s data
@audit_bp.route("/patient/<int:patient_id>", methods=["GET"])
@jwt_required()
def get_patient_access_logs(patient_id):
    try:
        # Only the patient or admin can view this
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if not current_user:
            return jsonify({"error": "User not found"}), 404

        if current_user.role != "admin":
            patient = Patient.query.filter_by(user_id=current_user_id).first()
            if not patient or patient.id != patient_id:
                return jsonify({"error": "Access denied"}), 403

        logs = AccessLog.query.filter_by(patient_id=patient_id).order_by(AccessLog.accessed_at.desc()).all()

        return jsonify([
            {
                "id": log.id,
                "user_id": log.user_id,
                "user_name": getattr(log.user, "username", None),
                "action": log.action,
                "timestamp": log.access_time.isoformat()
            }
            for log in logs
        ]), 200

    except Exception as e:
        logging.error("Error fetching patient access logs: %s", e)
        return jsonify({"error": "Failed to fetch patient logs"}), 500
