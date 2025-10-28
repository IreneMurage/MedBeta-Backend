from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity
from datetime import datetime
from app.db import db
from app.models import Doctor, Appointment, Patient, MedicalRecord, AccessLog
from app.utils.role_required import role_required

doctor_bp = Blueprint("doctor_bp", __name__, url_prefix="/doctors")


#  GET /doctors/profile — View doctor profile
@doctor_bp.route("/profile", methods=["GET"])
@role_required("doctor")
def get_doctor_profile():
    user_id = int(get_jwt_identity())
    doctor = Doctor.query.filter_by(user_id=user_id).first()

    if not doctor:
        return jsonify({"error": "Doctor profile not found"}), 404

    return jsonify({
        "message": "Doctor profile retrieved successfully.",
        "data": {
            "id": doctor.id,
            "name": doctor.user.name,
            "email": doctor.user.email,
            "specialization": doctor.specialization,
            "license_number": doctor.license_number,
            "hospital": doctor.hospital.name if doctor.hospital else None,
            "is_verified": doctor.is_verified,
            "is_active": doctor.is_active,
        }
    }), 200


# PUT /doctors/profile — Update doctor profile
@doctor_bp.route("/profile", methods=["PUT"])
@role_required("doctor")
def update_doctor_profile():
    user_id = int(get_jwt_identity())
    doctor = Doctor.query.filter_by(user_id=user_id).first()

    if not doctor:
        return jsonify({"error": "Doctor profile not found"}), 404

    data = request.get_json() or {}
    doctor.specialization = data.get("specialization", doctor.specialization)
    doctor.is_active = data.get("is_active", doctor.is_active)
    db.session.commit()

    return jsonify({"message": "Doctor profile updated successfully."}), 200


#  GET /doctors/appointments — View all appointments
@doctor_bp.route("/appointments", methods=["GET"])
@role_required("doctor")
def get_doctor_appointments():
    user_id = int(get_jwt_identity())
    doctor = Doctor.query.filter_by(user_id=user_id).first()

    if not doctor:
        return jsonify({"error": "Doctor profile not found"}), 404

    appointments = Appointment.query.filter_by(doctor_id=doctor.id).all()
    return jsonify({
        "message": "Appointments retrieved successfully.",
        "data": [
            {
                "id": a.id,
                "patient_id": a.patient.id,
                "patient_name": a.patient.user.name,
                "date": a.date.isoformat() if a.date else None,
                "status": a.status,
                "notes": a.notes,
            }
            for a in appointments
        ]
    }), 200


# PUT /doctors/appointments/<appointment_id>/status — Update appointment status
@doctor_bp.route("/appointments/<int:appointment_id>/status", methods=["PUT"])
@role_required("doctor")
def update_appointment_status(appointment_id):
    user_id = int(get_jwt_identity())
    doctor = Doctor.query.filter_by(user_id=user_id).first()

    if not doctor:
        return jsonify({"error": "Doctor profile not found"}), 404

    data = request.get_json() or {}
    new_status = data.get("status")

    valid_statuses = ["accepted", "declined", "completed"]
    if new_status not in valid_statuses:
        return jsonify({"error": f"Invalid status. Must be one of {valid_statuses}"}), 400

    appointment = Appointment.query.filter_by(id=appointment_id, doctor_id=doctor.id).first()
    if not appointment:
        return jsonify({"error": "Appointment not found"}), 404

    appointment.status = new_status
    db.session.commit()

    return jsonify({"message": f"Appointment status updated to '{new_status}'."}), 200


# POST /doctors/medical-records — Add or update a medical record
@doctor_bp.route("/medical-records", methods=["POST"])
@role_required("doctor")
def add_or_update_medical_record():
    user_id = int(get_jwt_identity())
    doctor = Doctor.query.filter_by(user_id=user_id).first()

    if not doctor:
        return jsonify({"error": "Doctor profile not found"}), 404

    data = request.get_json() or {}
    patient_id = data.get("patient_id")
    diagnosis = data.get("diagnosis")
    prescription = data.get("prescription")

    if not all([patient_id, diagnosis, prescription]):
        return jsonify({"error": "Missing required fields (patient_id, diagnosis, prescription)."}), 400

    record = MedicalRecord.query.filter_by(doctor_id=doctor.id, patient_id=patient_id).first()

    if record:
        record.diagnosis = diagnosis
        record.prescription = prescription
        record.updated_at = datetime.utcnow()
        message = "Medical record updated."
    else:
        new_record = MedicalRecord(
            doctor_id=doctor.id,
            patient_id=patient_id,
            diagnosis=diagnosis,
            prescription=prescription,
            created_at=datetime.utcnow(),
        )
        db.session.add(new_record)
        message = "Medical record added."

    db.session.commit()
    return jsonify({"message": message}), 201


# GET /doctors/patients — View all patients the doctor has seen
@doctor_bp.route("/patients", methods=["GET"])
@role_required("doctor")
def get_doctor_patients():
    user_id = int(get_jwt_identity())
    doctor = Doctor.query.filter_by(user_id=user_id).first()

    if not doctor:
        return jsonify({"error": "Doctor profile not found"}), 404

    patients = (
        db.session.query(Patient)
        .join(Appointment, Appointment.patient_id == Patient.id)
        .filter(Appointment.doctor_id == doctor.id)
        .distinct()
        .all()
    )

    return jsonify({
        "message": "Patients retrieved successfully.",
        "data": [
            {
                "id": p.id,
                "name": p.user.name,
                "email": p.user.email,
                "gender": getattr(p, "gender", None)
            }
            for p in patients
        ]
    }), 200


# GET /doctors/access-logs — View doctor’s access logs
@doctor_bp.route("/access-logs", methods=["GET"])
@role_required("doctor")
def get_access_logs():
    user_id = int(get_jwt_identity())
    doctor = Doctor.query.filter_by(user_id=user_id).first()

    if not doctor:
        return jsonify({"error": "Doctor profile not found"}), 404

    logs = AccessLog.query.filter_by(doctor_id=doctor.id).order_by(AccessLog.accessed_at.desc()).all()
    return jsonify({
        "message": "Access logs retrieved successfully.",
        "data": [
            {
                "id": log.id,
                "doctor_id": log.doctor_id,
                "patient_id": log.patient_id,
                "accessed_at": log.accessed_at.isoformat()
            }
            for log in logs
        ]
    }), 200
