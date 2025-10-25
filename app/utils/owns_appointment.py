from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from app.models import Appointment

def patient_owns_appointment(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(id, *args, **kwargs):
        identity = get_jwt_identity()
        appt = Appointment.query.get_or_404(id)
        if identity.get("id") != appt.patient_id:
            return jsonify({"error": "Not your appointment"}), 403
        return fn(id, *args, **kwargs)
    return wrapper

def doctor_owns_appointment(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(id, *args, **kwargs):
        identity = get_jwt_identity()
        appt = Appointment.query.get_or_404(id)
        if identity.get("id") != appt.doctor_id:
            return jsonify({"error": "Not your patient"}), 403
        return fn(id, *args, **kwargs)
    return wrapper
