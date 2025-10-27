from flask import Blueprint, request, jsonify
from app.db import db
from app.models import Appointment
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.utils.role_required import role_required
from app.utils.owns_appointment import patient_owns_appointment, doctor_owns_appointment

appointment_bp = Blueprint("appointments", __name__, url_prefix="/appointments")


# GET /appointments (Admin only)
@appointment_bp.route("/", methods=["GET"])
@role_required("admin")
def get_all_appointments():
    appointments = Appointment.query.all()
    return jsonify([{
        "id": appt.id,
        "patient_id": appt.patient_id,
        "doctor_id": appt.doctor_id,
        "hospital_id": appt.hospital_id,
        "date": str(appt.date),
        "time": str(appt.time),
        "status": appt.status
    } for appt in appointments]), 200


# GET /appointments/<id> (Admin or Patient Owner)
@appointment_bp.route("/<int:id>", methods=["GET"])
@role_required("admin", "patient", "doctor")
def get_appointment(id):
    identity = get_jwt_identity()
    user_id = int(identity)
    role = get_jwt().get("role")

    appt = Appointment.query.get_or_404(id)

    # Ownership Logic
    if role == "patient" and user_id != appt.patient_id:
        return jsonify({"error": "Not your appointment"}), 403
    if role == "doctor" and user_id != appt.doctor_id:
        return jsonify({"error": "Not your patient"}), 403

    return jsonify({
        "id": appt.id,
        "patient_id": appt.patient_id,
        "doctor_id": appt.doctor_id,
        "hospital_id": appt.hospital_id,
        "date": str(appt.date),
        "time": str(appt.time),
        "status": appt.status
    }), 200



# POST /appointments (Patients only)
@appointment_bp.route("/", methods=["POST"])
@role_required("patient")
def create_appointment():
    user_id = int(get_jwt_identity())
    data = request.json

    new_appt = Appointment(
        patient_id=user_id,
        doctor_id=data.get("doctor_id"),
        hospital_id=data.get("hospital_id"),
        date=data.get("date"),
        time=data.get("time")
    )

    db.session.add(new_appt)
    db.session.commit()
    return jsonify({"message": "Appointment created", "id": new_appt.id}), 201


# PUT /appointments/<id>
# Patient → Reschedule
# Doctor → Accept/Decline
# Admin → Full control
@appointment_bp.route("/<int:id>", methods=["PUT"])
@role_required("patient", "doctor", "admin")
def update_appointment(id):
    user_id = int(get_jwt_identity())
    role = get_jwt().get("role")

    appt = Appointment.query.get_or_404(id)
    data = request.json

    if role == "patient":
        if user_id != appt.patient_id:
            return jsonify({"error": "Not your appointment"}), 403
        appt.date = data.get("date", appt.date)
        appt.time = data.get("time", appt.time)

    elif role == "doctor":
        if user_id != appt.doctor_id:
            return jsonify({"error": "Not your patient"}), 403
        status = data.get("status")
        if status not in ["accepted", "declined"]:
            return jsonify({"error": "Doctors can only accept or decline"}), 400
        appt.status = status

    elif role == "admin":
        appt.date = data.get("date", appt.date)
        appt.time = data.get("time", appt.time)
        if "status" in data:
            appt.status = data["status"]

    db.session.commit()
    return jsonify({"message": "Appointment updated", "status": appt.status}), 200


# DELETE /appointments/<id> (Owner or Admin)
@appointment_bp.route("/<int:id>", methods=["DELETE"])
@role_required("patient", "admin")
@patient_owns_appointment
def delete_appointment(id):
    appt = Appointment.query.get_or_404(id)
    db.session.delete(appt)
    db.session.commit()
    return jsonify({"message": "Appointment cancelled"}), 200
