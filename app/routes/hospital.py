from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from sqlalchemy.exc import IntegrityError
from app.db import db
from app.models import Hospital, User, Doctor, Technician, Pharmacy, PendingUser
from app.utils.email_utils import send_invite_email
from app.utils.tokens import generate_token
from app.utils.time import utc_now
from app.utils.role_required import role_required
import csv, io, json

hospital_bp = Blueprint("hospital_bp", __name__)

# delete hospital — Superadmin only
@hospital_bp.delete("/hospitals/<int:id>")
@role_required("superadmin")
def delete_hospital(id):
    hospital = Hospital.query.get(id)
    if not hospital:
        return jsonify({"error": "Hospital not found"}), 404

    for doc in hospital.doctors:
        if doc.user:
            db.session.delete(doc.user)
    for pending in hospital.pending_users:
        db.session.delete(pending)

    db.session.delete(hospital)
    db.session.commit()
    return jsonify({"message": f"Hospital {id} deleted successfully"}), 200


# upload staff(CSV or JSON) — Hospital Admin only
@hospital_bp.post("/hospitals/<int:id>/upload-staff")
@role_required("hospital_admin","hospital")
def upload_staff(id):
    hospital = Hospital.query.get(id)
    if not hospital:
        return jsonify({"error": "Hospital not found"}), 404

    file = request.files.get("file")
    staff_data = []

    if file and file.filename.endswith(".csv"):
        stream = io.StringIO(file.stream.read().decode("utf-8"))
        reader = csv.DictReader(stream)
        staff_data = [row for row in reader]
    elif request.is_json:
        staff_data = request.get_json().get("staff", [])
    else:
        return jsonify({"error": "Invalid input format — must be CSV or JSON"}), 400

    invites_sent = []
    for staff in staff_data:
        name = staff.get("name")
        email = staff.get("email")
        role = staff.get("role")

        if not all([name, email, role]):
            continue

        if User.query.filter_by(email=email).first():
            continue 

        token = generate_token(email)
        pending = PendingUser(
            email=email,
            name=name,
            role=role,
            hospital_id=id,
            invite_token=token,
            expires_at=utc_now(),
        )
        db.session.add(pending)

        verify_link = f"{request.host_url}auth/setup-password/{token}"
        send_invite_email(email, name, role, verify_link)
        invites_sent.append(email)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Some emails already pending"}), 400

    return jsonify({
        "message": f"Invites sent to {len(invites_sent)} staff",
        "emails": invites_sent
    }), 201


# get staff— Hospital Admin or Superadmin
@hospital_bp.get("/hospitals/<int:id>/staff")
@role_required("hospital_admin", "superadmin","hospital")
def get_staff(id):
    hospital = Hospital.query.get(id)
    if not hospital:
        return jsonify({"error": "Hospital not found"}), 404

    doctors = [
        {"id": d.id, "name": d.user.name, "email": d.user.email, "role": "doctor"}
        for d in hospital.doctors
    ]
    techs = [
        {"id": t.id, "name": t.user.name, "email": t.user.email, "role": "labtech"}
        for t in Technician.query.filter_by(hospital_id=id).all()
    ]
    pharmas = [
        {"id": p.id, "name": p.user.name, "email": p.user.email, "role": "pharmacist"}
        for p in Pharmacy.query.filter_by(hospital_id=id).all()
    ]

    staff = doctors + techs + pharmas
    return jsonify(staff), 200


# get doctors — Any Authenticated Role
@hospital_bp.get("/hospitals/<int:id>/doctors")
@role_required("superadmin", "hospital_admin", "doctor", "pharmacist", "labtech","hospital")
def get_doctors(id):
    doctors = Doctor.query.filter_by(hospital_id=id).all()
    return jsonify([
        {"id": d.id, "name": d.user.name, "email": d.user.email} for d in doctors
    ]), 200


# get lab techs — Any Authenticated Role
@hospital_bp.get("/hospitals/<int:id>/labtechs")
@role_required("superadmin", "hospital_admin", "doctor", "pharmacist", "labtech","hospital")
def get_labtechs(id):
    techs = Technician.query.filter_by(hospital_id=id).all()
    return jsonify([
        {"id": t.id, "name": t.user.name, "email": t.user.email} for t in techs
    ]), 200


# get pharmacy — Any Authenticated Role
@hospital_bp.get("/hospitals/<int:id>/pharmacists")
@role_required("superadmin", "hospital_admin", "doctor", "pharmacist", "labtech","hospital")
def get_pharmacists(id):
    pharmas = Pharmacy.query.filter_by(hospital_id=id).all()
    return jsonify([
        {"id": p.id, "name": p.user.name, "email": p.user.email} for p in pharmas
    ]), 200


# Getting hospital information after signing the agreement
@hospital_bp.get("/hospitals/<int:id>")
@role_required("superadmin", "hospital_admin", "doctor", "labtech", "pharmacist","hospital")
def get_hospital(id):
    hospital = Hospital.query.get(id)
    if not hospital:
        return jsonify({"error": "Hospital not found"}), 404

    return jsonify({
        "id": hospital.id,
        "name": hospital.name,
        "location": hospital.location,
        "license_number": hospital.license_number,
        "is_verified": hospital.is_verified,
        "agreement_signed": getattr(hospital, "agreement_signed", False)
    }), 200


# Sign agreement — Hospital Admin or Superadmin
@hospital_bp.put("/hospitals/<int:id>/agreement")
@role_required("hospital_admin", "superadmin", "hospital")
def update_agreement(id):
    hospital = Hospital.query.get(id)
    if not hospital:
        return jsonify({"error": "Hospital not found"}), 404

    hospital.agreement_signed = True
    db.session.commit()

    return jsonify({
        "message": f"Hospital {hospital.name} has signed the Data-Sharing Agreement",
        "agreement_signed": True
    }), 200
