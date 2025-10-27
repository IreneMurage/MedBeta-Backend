from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask import Blueprint, request, jsonify
from app.db import db
from app.models import MedicalRecord, Appointment, Patient, Doctor
from app.utils.role_required import role_required
from app.utils.log_access import log_access

medical_bp = Blueprint("medical_bp", __name__, url_prefix="/medical-records")


# GET all records for a specific patient
@medical_bp.route("/patient/<int:patient_id>", methods=["GET"])
@jwt_required()
def get_records_for_patient(patient_id):
    user_id = int(get_jwt_identity())  # now string → convert to int
    claims = get_jwt()
    role = claims.get("role")

    if role == "patient" and user_id != patient_id:
        return jsonify({"error": "Unauthorized"}), 403

    if role == "doctor":
        appointment = Appointment.query.filter_by(
            patient_id=patient_id,
            doctor_id=user_id
        ).first()

        if not appointment:
            return jsonify({"error": "Doctor has no access to this patient's records"}), 403

        log_access(doctor_id=user_id, patient_id=patient_id)

    records = MedicalRecord.query.filter_by(patient_id=patient_id).all()

    return jsonify([
        {
            "id": r.id,
            "diagnosis": r.diagnosis,
            "treatment": r.treatment,
            "doctor_id": r.doctor_id,
            "appointment_id": r.appointment_id,
            "created_at": r.created_at.isoformat()
        }
        for r in records
    ]), 200


# POST — Doctor only
@medical_bp.route("/", methods=["POST"])
@role_required("doctor")
def create_record():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    patient_id = data.get("patient_id")
    appointment_id = data.get("appointment_id")

    if not patient_id:
        return jsonify({"error": "Missing patient_id"}), 400

    if appointment_id:
        appointment = Appointment.query.filter_by(
            id=appointment_id,
            doctor_id=user_id,
            patient_id=patient_id
        ).first()
        if not appointment:
            return jsonify({"error": "Invalid appointment"}), 403
    else:
        appointment = Appointment.query.filter_by(
            doctor_id=user_id, patient_id=patient_id
        ).first()
        if not appointment:
            return jsonify({"error": "Doctor has no appointments with this patient"}), 403

    new_record = MedicalRecord(
        patient_id=patient_id,
        doctor_id=user_id,
        appointment_id=appointment_id,
        diagnosis=data.get("diagnosis"),
        treatment=data.get("treatment"),
        notes=data.get("notes")
    )
    db.session.add(new_record)
    db.session.commit()

    return jsonify({"message": "Medical record created", "id": new_record.id}), 201


# PUT — Only owning doctor or admin
@medical_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
def update_record(id):
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role")
    data = request.get_json()

    record = MedicalRecord.query.get_or_404(id)

    if role == "doctor" and record.doctor_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403

    if role in ["admin", "superadmin"] or record.doctor_id == user_id:
        record.diagnosis = data.get("diagnosis", record.diagnosis)
        record.treatment = data.get("treatment", record.treatment)
        record.notes = data.get("notes", record.notes)
        db.session.commit()
        return jsonify({"message": "Record updated"}), 200

    return jsonify({"error": "Forbidden"}), 403


# DELETE — Admin
@medical_bp.route("/<int:id>", methods=["DELETE"])
@role_required("admin", "superadmin")
def delete_record(id):
    record = MedicalRecord.query.get_or_404(id)
    db.session.delete(record)
    db.session.commit()
    return jsonify({"message": "Record deleted"}), 200
