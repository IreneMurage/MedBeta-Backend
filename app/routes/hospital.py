from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError
from app.db import db
from app.models import Hospital, User, Doctor, Technician, Pharmacy, PendingUser
from app.utils.email_utils import send_invite_email
from app.utils.tokens import generate_token
from app.utils.time import utc_now
import csv, io, json

hospital_bp = Blueprint("hospital_bp", __name__)

# DELETE /hospitals/<id> — Superadmin only
@hospital_bp.route("/hospitals/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_hospital(id):
    current = get_jwt_identity()
    if current["role"] != "superadmin":
        return jsonify({"error": "Unauthorized"}), 403

    hospital = Hospital.query.get(id)
    if not hospital:
        return jsonify({"error": "Hospital not found"}), 404

    # Delete linked users
    for doc in hospital.doctors:
        db.session.delete(doc.user)
    for pending in hospital.pending_users:
        db.session.delete(pending)

    db.session.delete(hospital)
    db.session.commit()
    return jsonify({"message": f"Hospital {id} deleted successfully"}), 200


# POST /hospitals/<id>/upload-staff — Hospital Admin uploads staff invites
@hospital_bp.route("/hospitals/<int:id>/upload-staff", methods=["POST"])
@jwt_required()
def upload_staff(id):
    current = get_jwt_identity()
    if current["role"] != "hospital_admin":
        return jsonify({"error": "Unauthorized"}), 403

    hospital = Hospital.query.get(id)
    if not hospital:
        return jsonify({"error": "Hospital not found"}), 404

    # Expect CSV or JSON
    file = request.files.get("file")
    staff_data = []

    if file and file.filename.endswith(".csv"):
        stream = io.StringIO(file.stream.read().decode("utf-8"))
        reader = csv.DictReader(stream)
        staff_data = [row for row in reader]
    elif request.is_json:
        staff_data = request.get_json().get("staff", [])
    else:
        return jsonify({"error": "Invalid input format"}), 400

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


# GET /hospitals/<id>/staff
@hospital_bp.route("/hospitals/<int:id>/staff", methods=["GET"])
@jwt_required()
def get_staff(id):
    current = get_jwt_identity()
    if current["role"] not in ("hospital_admin", "superadmin"):
        return jsonify({"error": "Unauthorized"}), 403

    hospital = Hospital.query.get(id)
    if not hospital:
        return jsonify({"error": "Hospital not found"}), 404

    doctors = [{"id": d.id, "name": d.user.name, "email": d.user.email, "role": "doctor"} for d in hospital.doctors]
    techs = [{"id": t.id, "name": t.user.name, "email": t.user.email, "role": "labtech"} for t in Technician.query.filter_by(hospital_id=id).all()]
    pharmas = [{"id": p.id, "name": p.user.name, "email": p.user.email, "role": "pharmacist"} for p in Pharmacy.query.filter_by(hospital_id=id).all()]

    staff = doctors + techs + pharmas
    return jsonify(staff), 200


# GET /hospitals/<id>/doctors
@hospital_bp.route("/hospitals/<int:id>/doctors", methods=["GET"])
@jwt_required()
def get_doctors(id):
    doctors = Doctor.query.filter_by(hospital_id=id).all()
    return jsonify([{"id": d.id, "name": d.user.name, "email": d.user.email} for d in doctors]), 200


# GET /hospitals/<id>/labtechs
@hospital_bp.route("/hospitals/<int:id>/labtechs", methods=["GET"])
@jwt_required()
def get_labtechs(id):
    techs = Technician.query.filter_by(hospital_id=id).all()
    return jsonify([{"id": t.id, "name": t.user.name, "email": t.user.email} for t in techs]), 200


# GET /hospitals/<id>/pharmacists
@hospital_bp.route("/hospitals/<int:id>/pharmacists", methods=["GET"])
@jwt_required()
def get_pharmacists(id):
    pharmas = Pharmacy.query.filter_by(hospital_id=id).all()
    return jsonify([{"id": p.id, "name": p.user.name, "email": p.user.email} for p in pharmas]), 200


# GET /hospitals/<id> — Get hospital info (includes agreement status)
@hospital_bp.route("/hospitals/<int:id>", methods=["GET"])
@jwt_required()
def get_hospital(id):
    current = get_jwt_identity()
    hospital = Hospital.query.get(id)

    if not hospital:
        return jsonify({"error": "Hospital not found"}), 404

    # Allow hospital admin, superadmin, or linked hospital users
    if current["role"] not in ("superadmin", "hospital_admin") and current.get("hospital_id") != id:
        return jsonify({"error": "Unauthorized"}), 403

    return jsonify({
        "id": hospital.id,
        "name": hospital.name,
        "location": hospital.location,
        "license_number": hospital.license_number,
        "is_verified": hospital.is_verified,
        "agreement_signed": getattr(hospital, "agreement_signed", False)
    }), 200


# PUT /hospitals/<id>/agreement — Sign data-sharing agreement
@hospital_bp.route("/hospitals/<int:id>/agreement", methods=["PUT"])
@jwt_required()
def update_agreement(id):
    current = get_jwt_identity()
    hospital = Hospital.query.get(id)

    if not hospital:
        return jsonify({"error": "Hospital not found"}), 404

    # Only hospital admins or superadmins can sign
    if current["role"] not in ("hospital_admin", "superadmin"):
        return jsonify({"error": "Unauthorized"}), 403

    hospital.agreement_signed = True
    db.session.commit()

    return jsonify({
        "message": f"Hospital {hospital.name} has signed the Data-Sharing Agreement",
        "agreement_signed": True
    }), 200
