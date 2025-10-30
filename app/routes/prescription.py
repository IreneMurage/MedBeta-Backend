from flask import Blueprint, request, jsonify
from app.db import db
from app.models.prescriptions import Prescription
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.Pharmacy import Pharmacy
from datetime import datetime
from app.utils.role_required import role_required  

prescription_bp = Blueprint("prescription_bp", __name__)

# creating prescriptions(Doctor → Pharmacy)
@prescription_bp.post("/prescriptions")
@role_required("doctor")  
def create_prescription():
    data = request.get_json()

    doctor_id = data.get("doctor_id")
    patient_id = data.get("patient_id")
    medication_details = data.get("medication_details")

    if not all([doctor_id, patient_id, medication_details]):
        return jsonify({"error": "doctor_id, patient_id, and medication_details are required"}), 400

    doctor = Doctor.query.get(doctor_id)
    patient = Patient.query.get(patient_id)

    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    new_prescription = Prescription(
        doctor_id=doctor_id,
        patient_id=patient_id,
        medication_details=medication_details
    )

    db.session.add(new_prescription)
    db.session.commit()

    return jsonify({
        "message": "Prescription created successfully and sent to pharmacy",
        "prescription": {
            "id": new_prescription.id,
            "doctor_id": doctor_id,
            "patient_id": patient_id,
            "medication_details": medication_details,
            "issued_date": new_prescription.issued_date
        }
    }), 201

@prescription_bp.get("/prescriptions/unclaimed")
@role_required("pharmacist")
def get_unclaimed_prescriptions():
    prescriptions = Prescription.query.filter_by(pharmacy_id=None).order_by(Prescription.issued_date.desc()).all()

    result = []
    for p in prescriptions:
        result.append({
            "id": p.id,
            "doctor": p.doctor.user.name if p.doctor and p.doctor.user else "Unknown Doctor",
            "patient": p.patient.user.name if p.patient and p.patient.user else "Unknown Patient",
            "medication_details": p.medication_details,
            "issued_date": p.issued_date,
        })

    return jsonify(result), 200

from flask_jwt_extended import get_jwt_identity

@prescription_bp.get("/prescriptions/pharmacy")
@role_required("pharmacist")
def get_pharmacy_prescriptions():
    current_user_id = int(get_jwt_identity())
    pharmacy = Pharmacy.query.filter_by(user_id=current_user_id).first()
    if not pharmacy:
        return jsonify({"error": "Pharmacy not found"}), 404

    prescriptions = Prescription.query.filter_by(pharmacy_id=pharmacy.id).order_by(Prescription.issued_date.desc()).all()
    result = [{
        "id": p.id,
        "doctor": p.doctor.user.name if p.doctor and p.doctor.user else "Unknown Doctor",
        "patient": p.patient.user.name if p.patient and p.patient.user else "Unknown Patient",
        "medication_details": p.medication_details,
        "issued_date": p.issued_date,
    } for p in prescriptions]

    return jsonify(result), 200

@prescription_bp.put("/prescriptions/<int:prescription_id>/claim")
@role_required("pharmacist")
def claim_prescription(prescription_id):
    current_user_id = int(get_jwt_identity())  # this is the logged-in user id
    pharmacy = Pharmacy.query.filter_by(user_id=current_user_id).first()
    if not pharmacy:
        return jsonify({"error": "Pharmacy not found for current user"}), 404

    prescription = Prescription.query.get(prescription_id)
    if not prescription:
        return jsonify({"error": "Prescription not found"}), 404

    if prescription.pharmacy_id is not None:
        return jsonify({"error": "Prescription already claimed"}), 400

    prescription.pharmacy_id = pharmacy.id  # use correct pharmacy id
    db.session.commit()

    return jsonify({
        "message": "Prescription claimed successfully",
        "prescription_id": prescription.id,
        "pharmacy_id": pharmacy.id
    }), 200


# get prescriptions(only Pharmacy & Admin can View)
@prescription_bp.get("/prescriptions")
@role_required("pharmacist", "admin")
def get_all_prescriptions():
    prescriptions = Prescription.query.order_by(Prescription.issued_date.desc()).all()
    result = []

    for p in prescriptions:
        result.append({
            "id": p.id,
            "doctor": p.doctor.user.name if p.doctor and p.doctor.user else "Unknown Doctor",
            "patient": p.patient.user.name if p.patient and p.patient.user else "Unknown Patient",
            "medication_details": p.medication_details,
            "issued_date": p.issued_date,
        })

    return jsonify(result), 200


# get prescription for a specific patient
@prescription_bp.get("/prescriptions/patient/<int:patient_id>")
@role_required("patient", "doctor", "admin")
def get_prescriptions_by_patient(patient_id):
    prescriptions = Prescription.query.filter_by(patient_id=patient_id).all()
    if not prescriptions:
        return jsonify({"message": "No prescriptions found for this patient"}), 404

    result = [{
        "id": p.id,
        "doctor": p.doctor.user.name if p.doctor and p.doctor.user else "Unknown Doctor",
        "medication_details": p.medication_details,
        "issued_date": p.issued_date,
    } for p in prescriptions]

    return jsonify(result), 200


#get prescription by doctor
@prescription_bp.get("/prescriptions/doctor/<int:doctor_id>")
@role_required("doctor", "admin")
def get_prescriptions_by_doctor(doctor_id):
    prescriptions = Prescription.query.filter_by(doctor_id=doctor_id).all()
    if not prescriptions:
        return jsonify({"message": "No prescriptions found for this doctor"}), 404

    result = [{
        "id": p.id,
        "patient": p.patient.user.name if p.patient and p.patient.user else "Unknown Patient",
        "medication_details": p.medication_details,
        "issued_date": p.issued_date,
    } for p in prescriptions]

    return jsonify(result), 200


# Delete prescription (Doctor/Admin only)
@prescription_bp.delete("/prescriptions/<int:id>")
@role_required("doctor", "admin")
def delete_prescription(id):
    prescription = Prescription.query.get(id)
    if not prescription:
        return jsonify({"error": "Prescription not found"}), 404

    db.session.delete(prescription)
    db.session.commit()

    return jsonify({"message": f"Prescription {id} deleted successfully"}), 200
