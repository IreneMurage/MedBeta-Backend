from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.db import db
from app.models import Doctor, Appointment, Patient, MedicalRecord, AccessLog, User
from app.decorators import role_required

doctor_bp = Blueprint("doctor_bp", __name__)

# 🩺 GET /doctors/<id> — View doctor profile
@doctor_bp.route("/<int:id>", methods=["GET"])
@jwt_required()
@role_required("doctor")
def get_doctor_profile(id):
    doctor = Doctor.query.get_or_404(id)
    data = {
        "id": doctor.id,
        "name": doctor.user.name,
        "email": doctor.user.email,
        "specialization": doctor.specialization,
        "license_number": doctor.license_number,
        "hospital": doctor.hospital.name if doctor.hospital else None,
        "is_verified": doctor.is_verified,
        "is_active": doctor.is_active,
    }
    return jsonify(data), 200


# 🩺 PUT /doctors/<id> — Update doctor profile
@doctor_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
@role_required("doctor")
def update_doctor_profile(id):
    doctor = Doctor.query.get_or_404(id)
    data = request.get_json()

    doctor.specialization = data.get("specialization", doctor.specialization)
    doctor.is_active = data.get("is_active", doctor.is_active)
    db.session.commit()

    return jsonify({"message": "Doctor profile updated successfully."}), 200


# GET /doctors/<id>/appointments — Get all appointments for doctor
@doctor_bp.route("/<int:id>/appointments", methods=["GET"])
@jwt_required()
@role_required("doctor")
def get_doctor_appointments(id):
    appointments = Appointment.query.filter_by(doctor_id=id).all()

    return jsonify([
        {
            "id": a.id,
            "patient_id": a.patient.id,
            "patient_name": a.patient.user.name,
            "date": a.date.isoformat() if a.date else None,
            "status": a.status,
            "notes": a.notes,
        }
        for a in appointments
    ]), 200


# ✅ PUT /doctors/<id>/appointments/<appointment_id>/status — Update appointment status
@doctor_bp.route("/<int:id>/appointments/<int:appointment_id>/status", methods=["PUT"])
@jwt_required()
@role_required("doctor")
def update_appointment_status(id, appointment_id):
    data = request.get_json()
    new_status = data.get("status")

    valid_statuses = ["accepted", "declined", "completed"]
    if new_status not in valid_statuses:
        return jsonify({"error": f"Invalid status. Must be one of {valid_statuses}"}), 400

    appointment = Appointment.query.filter_by(id=appointment_id, doctor_id=id).first_or_404()
    appointment.status = new_status
    db.session.commit()

    return jsonify({"message": f"Appointment status updated to '{new_status}'."}), 200


#  POST /doctors/<id>/medical-records — Add or update a medical record
@doctor_bp.route("/<int:id>/medical-records", methods=["POST"])
@jwt_required()
@role_required("doctor")
def add_or_update_medical_record(id):
    data = request.get_json()
    patient_id = data.get("patient_id")
    diagnosis = data.get("diagnosis")
    prescription = data.get("prescription")

    if not all([patient_id, diagnosis, prescription]):
        return jsonify({"error": "Missing required fields (patient_id, diagnosis, prescription)."}), 400

    record = MedicalRecord.query.filter_by(doctor_id=id, patient_id=patient_id).first()

    if record:
        record.diagnosis = diagnosis
        record.prescription = prescription
        record.updated_at = datetime.utcnow()
        message = "Medical record updated."
    else:
        new_record = MedicalRecord(
            doctor_id=id,
            patient_id=patient_id,
            diagnosis=diagnosis,
            prescription=prescription,
            created_at=datetime.utcnow(),
        )
        db.session.add(new_record)
        message = "Medical record added."

    db.session.commit()
    return jsonify({"message": message}), 201


# 👩‍⚕️ GET /doctors/<id>/patients — View all patients seen by the doctor
@doctor_bp.route("/<int:id>/patients", methods=["GET"])
@jwt_required()
@role_required("doctor")
def get_doctor_patients(id):
    patients = (
        db.session.query(Patient)
        .join(Appointment, Appointment.patient_id == Patient.id)
        .filter(Appointment.doctor_id == id)
        .distinct()
        .all()
    )

    return jsonify([
        {
            "id": p.id,
            "name": p.user.name,
            "email": p.user.email,
            "gender": p.gender if hasattr(p, "gender") else None
        }
        for p in patients
    ]), 200


# 📜 GET /doctors/<id>/access-logs — View audit trail of which patient files the doctor accessed
@doctor_bp.route("/<int:id>/access-logs", methods=["GET"])
@jwt_required()
@role_required("doctor")
def get_access_logs(id):
    logs = AccessLog.query.filter_by(doctor_id=id).order_by(AccessLog.accessed_at.desc()).all()

    return jsonify([
        {
            "id": log.id,
            "doctor_id": log.doctor_id,
            "patient_id": log.patient_id,
            "accessed_at": log.accessed_at.isoformat()
        }
        for log in logs
    ]), 200
