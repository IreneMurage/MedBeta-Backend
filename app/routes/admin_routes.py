from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from uuid import uuid4
from datetime import datetime, timedelta
from app.db import db
from app.models import PendingUser, User, Hospital, AccessLog
from app.utils.role_required import role_required
from app.utils.email_utils import send_invite_email

superadmin_bp = Blueprint("superadmin_bp", __name__, url_prefix="/admin")


#  POST /admin/invite-user
@superadmin_bp.route("/invite-user", methods=["POST"])
@role_required("superadmin")
def invite_user():
    data = request.get_json()
    # print("DEBUG data:", data, type(data))
    email = data.get("email")
    name = data.get("name")
    role = data.get("role")
    hospital_id = data.get("hospital_id")  # optional

    # Validate input
    if not email or not role or not name:
        return jsonify({"error": "Missing required fields (email, name, role)"}), 400

    # Prevent duplicates
    if PendingUser.query.filter_by(email=email).first() or User.query.filter_by(email=email).first():
        return jsonify({"error": "A user with this email already exists"}), 400

    # Create a unique token
    token = str(uuid4())
    expires_at = datetime.utcnow() + timedelta(days=7)

    # Store pending invite
    pending = PendingUser(
        email=email,
        name=name,
        role=role,
        hospital_id=hospital_id,
        invite_token=token,
        expires_at=expires_at,
        is_accepted=False,
    )
    db.session.add(pending)
    db.session.commit()

    # Send invitation email
    try:
        sent = send_invite_email(email, token)
        if not sent:
            return jsonify({
                # "warning": "Invite created but email not sent (check SendGrid config)",
                "invite_token": token
            }), 201
    except Exception as e:
        print(f"Email error: {e}")
        return jsonify({
            "warning": "Invite created, but failed to send email",
            "invite_token": token
        }), 201

    # Return success response
    return jsonify({
        "message": f"Invite sent to {email} successfully",
        "invite_token": token,
        "expires_at": expires_at.isoformat()
    }), 201


#  GET /admin/pending-invites
@superadmin_bp.route("/pending-invites", methods=["GET"])
@role_required("superadmin")
def pending_invites():
    invites = PendingUser.query.filter_by(is_accepted=False).all()
    return jsonify([{
        "id": inv.id,
        "email": inv.email,
        "role": inv.role,
        "hospital_id": inv.hospital_id,
        "is_accepted": inv.is_accepted,
        "expires_at": inv.expires_at.isoformat() if inv.expires_at else None
    } for inv in invites]), 200


#  GET /admin/pending-hospitals
@superadmin_bp.route("/pending-hospitals", methods=["GET"])
@role_required("superadmin")
def pending_hospitals():
    hospitals = Hospital.query.filter_by(is_verified=False).all()
    return jsonify([{
        "id": h.id,
        "name": h.name,
        "email": h.user.email if h.user else None
    } for h in hospitals]), 200


#  PUT /admin/approve-hospital/<id>
@superadmin_bp.route("/approve-hospital/<int:id>", methods=["PUT"])
@role_required("superadmin")
def approve_hospital(id):
    hospital = Hospital.query.get_or_404(id)
    hospital.is_verified = True
    db.session.commit()
    # Optional: send invite to hospital admin
    return jsonify({"message": f"Hospital {hospital.name} approved"}), 200

# GET /admin/pending-staff
@superadmin_bp.route("/pending-staff", methods=["GET"])
@role_required("superadmin")
def pending_staff():
    # Define which staff roles to include
    roles = ["doctor", "technician", "lab_tech", "pharmacist"]

    # Filter pending users who match these roles and haven't accepted yet
    pending = PendingUser.query.filter(
        PendingUser.role.in_(roles),
        PendingUser.is_accepted == False
    ).all()

    # Return a structured JSON list
    return jsonify([
        {
            "id": p.id,
            "name": p.name,
            "email": p.email,
            "role": p.role,
            "hospital_id": p.hospital_id,
            "hospital_name": p.hospital.name if p.hospital else None,
            "created_at": p.created_at.isoformat(),
            "expires_at": p.expires_at.isoformat() if p.expires_at else None,
        }
        for p in pending
    ]), 200

#  GET /admin/pending-doctors
@superadmin_bp.route("/pending-doctors", methods=["GET"])
@role_required("superadmin")
def pending_doctors():
    pending = PendingUser.query.filter_by(role="doctor", is_accepted=False).all()
    return jsonify([{
        "id": p.id,
        "name": p.name,
        "email": p.email,
        "hospital_id": p.hospital_id
    } for p in pending]), 200

@superadmin_bp.route("/users", methods=["GET"])
@role_required("superadmin")
def get_all_users():
    """
    Get all users in the system except hospital accounts.
    """
    # Exclude hospital admins — assuming role='hospital' is used for them
    users = User.query.filter(User.role != "hospital").all()

    return jsonify([
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role,
            "status": u.status,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ]), 200


#  PUT /admin/approve-doctor/<id>
@superadmin_bp.route("/approve-doctor/<int:id>", methods=["PUT"])
@role_required("superadmin")
def approve_doctor(id):
    pending = PendingUser.query.get_or_404(id)
    pending.is_accepted = True
    db.session.commit()
    # Optional: send invite email
    send_invite_email(pending.email, pending.invite_token)
    return jsonify({"message": f"Doctor {pending.name} approved"}), 200


#  PUT /admin/reject-doctor/<id>
@superadmin_bp.route("/reject-doctor/<int:id>", methods=["PUT"])
@role_required("superadmin")
def reject_doctor(id):
    pending = PendingUser.query.get_or_404(id)
    db.session.delete(pending)
    db.session.commit()
    return jsonify({"message": f"Doctor {pending.name} rejected"}), 200

#  GET /admin/overview
@superadmin_bp.route("/overview", methods=["GET"])
@role_required("superadmin")
def overview():
    total_users = User.query.count()
    total_patients = User.query.filter_by(role="patient").count()
    total_doctors = User.query.filter_by(role="doctor").count()
    total_hospitals = Hospital.query.count()
    pending_invites = PendingUser.query.filter_by(is_accepted=False).count()

    return jsonify({
        "total_users": total_users,
        "total_patients": total_patients,
        "total_doctors": total_doctors,
        "total_hospitals": total_hospitals,
        "pending_invites": pending_invites
    }), 200

#  GET /admin/access-logs
@superadmin_bp.route("/access-logs", methods=["GET"])
@role_required("superadmin")
def access_logs():
    logs = AccessLog.query.order_by(AccessLog.accessed_at.desc()).all()
    return jsonify([
        {
            "id": log.id,
            "doctor_id": log.doctor_id,
            "doctor_name": log.doctor.user.name if log.doctor else None,
            "patient_id": log.patient_id,
            "patient_name": log.patient.user.name if log.patient else None,
            "accessed_at": str(log.accessed_at),
            "purpose": log.purpose
        } for log in logs
    ]), 200

#  Bulk upload staff (Superadmin)

@superadmin_bp.route("/upload-staff", methods=["POST"])
@role_required("superadmin")
def upload_staff():
    """
    Allows Superadmin to upload a CSV or JSON list of users (staff) for any hospital.
    Each invite creates a PendingUser record and sends an email with a verification link.
    """
    file = request.files.get("file")
    data = request.get_json() if request.is_json else None
    staff_data = []

    if file and file.filename.endswith(".csv"):
        import csv, io
        stream = io.StringIO(file.stream.read().decode("utf-8"))
        reader = csv.DictReader(stream)
        staff_data = [row for row in reader]
    elif data:
        staff_data = data.get("staff", [])
    else:
        return jsonify({"error": "Please upload a CSV file or JSON with 'staff' key"}), 400

    if not staff_data:
        return jsonify({"error": "No staff data found"}), 400

    invites_sent = []
    for person in staff_data:
        email = person.get("email")
        name = person.get("name")
        role = person.get("role")
        hospital_id = person.get("hospital_id")

        if not all([email, name, role]):
            continue

        # Skip if user or pending already exists
        if User.query.filter_by(email=email).first() or PendingUser.query.filter_by(email=email).first():
            continue

        # Generate unique token
        token = str(uuid4())
        expires_at = datetime.utcnow() + timedelta(days=7)

        pending = PendingUser(
            email=email,
            name=name,
            role=role,
            hospital_id=hospital_id,
            invite_token=token,
            expires_at=expires_at,
            is_accepted=False,
        )
        db.session.add(pending)

        # Email invite link
        verify_link = f"{request.host_url}auth/setup-password/{token}"
        try:
            send_invite_email(email, token)
        except Exception as e:
            print(f"Failed to send email to {email}: {e}")
        invites_sent.append(email)

    db.session.commit()

    return jsonify({
        "message": f"Invites sent successfully to {len(invites_sent)} users",
        "emails": invites_sent
    }), 201


@superadmin_bp.route("/hospitals", methods=["GET"])
@role_required("superadmin")
def get_hospitals():
    try:
        hospitals = Hospital.query.all()
        return jsonify([
            {
                "id": h.id,
                "name": h.name,
                "email": h.user.email if h.user else None,
                "location": h.location,
                "license_number": h.license_number,
                "is_verified": h.is_verified,
                "agreement_signed": h.agreement_signed,
            }
            for h in hospitals
        ]), 200
    except Exception as e:
        print(f"Error fetching hospitals: {e}")
        return jsonify({"error": "Failed to retrieve hospitals"}), 500

