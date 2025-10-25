from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.db import db
from app.models import MedicalRecord, Appointment, Patient, Doctor
from app.utils.role_required import role_required
from app.utils.log_access import log_access

medical_bp = Blueprint("medical_bp", __name__, url_prefix="/medical-records")

# GET all records for a specific patient
@medical_bp.route("/patient/<int:patient_id>", methods=["GET"])
@jwt_required()
def get_records_for_patient(patient_id):
    identity = get_jwt_identity()
    role = identity["role"]
    user_id = identity["id"]

    # Patients can only view their own records
    if role == "patient" and user_id != patient_id:
        return jsonify({"error": "Unauthorized"}), 403

    # Doctors must have at least one appointment with the patient
    if role == "doctor":
        appointment = Appointment.query.filter_by(patient_id=patient_id, doctor_id=user_id).first()
        if not appointment:
            return jsonify({"error": "Doctor has no access to this patient's records"}), 403
        
        log_access(doctor_id=user_id, patient_id=patient_id, purpose="viewed medical record")

    # Admins or authorized patients/doctors
    records = MedicalRecord.query.filter_by(patient_id=patient_id).all()
    return jsonify([{
        "id": r.id,
        "diagnosis": r.diagnosis,
        "treatment": r.treatment,
        "doctor_id": r.doctor_id,
        "appointment_id": r.appointment_id,
        "created_at": str(r.created_at)
    } for r in records]), 200


#  POST create new medical record (DOCTOR only)
@medical_bp.route("/", methods=["POST"])
@role_required("doctor")
def create_record():
    identity = get_jwt_identity()
    doctor_id = identity.get("id")
    data = request.get_json()

    patient_id = data.get("patient_id")
    appointment_id = data.get("appointment_id")  # optional but recommended

    if not patient_id:
        return jsonify({"error": "Missing patient_id"}), 400

    # If appointment_id is provided, validate it
    if appointment_id:
        appointment = Appointment.query.filter_by(
            id=appointment_id,
            doctor_id=doctor_id,
            patient_id=patient_id
        ).first()
        if not appointment:
            return jsonify({"error": "Invalid appointment. Doctor cannot create record for this patient"}), 403
    else:
        # Optional: allow creating record without appointment but check doctor has ever seen the patient
        appointment = Appointment.query.filter_by(
            doctor_id=doctor_id,
            patient_id=patient_id
        ).first()
        if not appointment:
            return jsonify({"error": "Doctor has no appointments with this patient"}), 403

    new_record = MedicalRecord(
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_id=appointment_id,
        diagnosis=data.get("diagnosis"),
        treatment=data.get("treatment"),
        notes=data.get("notes")
    )

    db.session.add(new_record)
    db.session.commit()

    return jsonify({"message": "Medical record created", "id": new_record.id}), 201


# PUT update medical record (Only OWN doctor or admin)
@medical_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
def update_record(id):
    identity = get_jwt_identity()
    record = MedicalRecord.query.get_or_404(id)

    role = identity.get("role")
    user_id = identity.get("id")
    data = request.get_json()

    # Doctor must own the record to update
    if role == "doctor" and record.doctor_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403

    # Admin can update everything
    if role == "admin" or record.doctor_id == user_id:
        record.diagnosis = data.get("diagnosis", record.diagnosis)
        record.treatment = data.get("treatment", record.treatment)
        record.notes = data.get("notes", record.notes)
        db.session.commit()
        return jsonify({"message": "Record updated"}), 200

    return jsonify({"error": "Unauthorized role"}), 403


#  DELETE medical record (ADMIN only)
@medical_bp.route("/<int:id>", methods=["DELETE"])
@role_required("admin")
def delete_record(id):
    record = MedicalRecord.query.get_or_404(id)
    db.session.delete(record)
    db.session.commit()
    return jsonify({"message": "Record deleted"}), 200
