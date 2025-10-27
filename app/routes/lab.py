from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.db import db
from app.models import Technician, TestRequest, User, Patient
from app.utils.role_required import role_required

lab_bp = Blueprint("lab_bp", __name__)


@lab_bp.route("/labtests", methods=["GET"])
@jwt_required()
@role_required("technician")
def get_assigned_tests():
    user_id = get_jwt_identity()
    technician = Technician.query.filter_by(user_id=user_id).first_or_404()

    tests = TestRequest.query.filter_by(technician_id=technician.id, status="Pending").all()
    return jsonify([
        {
            "id": t.id,
            "test_name": t.test_name,
            "patient_name": t.patient.user.name if t.patient and t.patient.user else None,
            "status": t.status,
            "date_requested": t.date_requested.isoformat() if t.date_requested else None,
            "doctor_name": t.doctor.user.name if t.doctor and t.doctor.user else None
        } for t in tests
    ]), 200

# -----------------------------
# 🧪 POST /labtests/<id>/update — Submit test results or mark test as complete
# -----------------------------
@lab_bp.route("/labtests/<int:id>/update", methods=["POST"])
@jwt_required()
@role_required("technician")
def update_test(id):
    user_id = get_jwt_identity()
    technician = Technician.query.filter_by(user_id=user_id).first_or_404()
    data = request.get_json()

    test = TestRequest.query.filter_by(id=id, technician_id=technician.id).first_or_404()

    status = data.get("status")
    if status and status not in ["Pending", "Completed"]:
        return jsonify({"error": "Invalid status. Must be 'Pending' or 'Completed'."}), 400

    results = data.get("results")  # optional field for test result details

    if results:
        test.results = results  # if your TestRequest model has a results field
    if status:
        test.status = status
        test.date_completed = datetime.utcnow() if status == "Completed" else None

    db.session.commit()
    return jsonify({"message": "Test request updated successfully."}), 200

# -----------------------------
#  GET /labtests/history — Completed tests history for the technician

@lab_bp.route("/labtests/history", methods=["GET"])
@jwt_required()
@role_required("technician")
def completed_tests_history():
    user_id = get_jwt_identity()
    technician = Technician.query.filter_by(user_id=user_id).first_or_404()

    completed_tests = TestRequest.query.filter_by(technician_id=technician.id, status="Completed")\
        .order_by(TestRequest.date_completed.desc()).all()

    return jsonify([
        {
            "id": t.id,
            "test_name": t.test_name,
            "patient_name": t.patient.user.name if t.patient and t.patient.user else None,
            "status": t.status,
            "date_requested": t.date_requested.isoformat() if t.date_requested else None,
            "date_completed": t.date_completed.isoformat() if t.date_completed else None,
            "doctor_name": t.doctor.user.name if t.doctor and t.doctor.user else None
        } for t in completed_tests
    ]), 200
