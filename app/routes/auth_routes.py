from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
from app.db import db
from app.models import User, PendingUser, Patient, Doctor, Hospital, Pharmacy, Technician
from app.utils.email_utils import send_invite_email, send_reset_email
from app.utils.tokens import generate_token, verify_token
from app.utils.time import utc_now

auth_bp = Blueprint("auth_bp", __name__)

#  POST /auth/register  -> Patients self-register
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"error": "Missing required fields"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists"}), 400

    # Create user
    user = User(name=name, email=email, role="patient")
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    # Create linked patient profile
    patient = Patient(user_id=user.id)
    db.session.add(patient)
    db.session.commit()

    access_token = create_access_token(
        identity={"id": user.id, "role": user.role}, expires_delta=timedelta(days=1)
    )
    return jsonify({"message": "Registration successful", "token": access_token}), 201

#  POST /auth/login  -> All roles
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    if not user.is_active:
        return jsonify({"error": "Account deactivated"}), 403

    token = create_access_token(
        identity={"id": user.id, "role": user.role}, expires_delta=timedelta(days=1)
    )
    return jsonify({"token": token, "role": user.role}), 200

#  POST /auth/logout  - Client logs out
@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    current_user = get_jwt_identity()
    return jsonify({"message": f"User {current_user['id']} logged out successfully"}), 200


#  PUT /auth/reset-password  -> Send password reset link
@auth_bp.route("/reset-password", methods=["PUT"])
def reset_password():
    data = request.get_json()
    email = data.get("email")

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    token = generate_token(email)
    send_reset_email(email, token)
    return jsonify({"message": "Password reset link sent"}), 200

#  PUT /auth/change-password  -> Authenticated user
@auth_bp.route("/change-password", methods=["PUT"])
@jwt_required()
def change_password():
    data = request.get_json()
    old_password = data.get("old_password")
    new_password = data.get("new_password")

    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user.check_password(old_password):
        return jsonify({"error": "Incorrect old password"}), 400

    user.set_password(new_password)
    db.session.commit()
    return jsonify({"message": "Password changed successfully"}), 200


#  GET /auth/setup-password/<token>  -> Invite activation
@auth_bp.route("/setup-password/<token>", methods=["GET", "POST"])
def setup_password(token):
    pending = PendingUser.query.filter_by(invite_token=token, is_accepted=False).first()

    if not pending:
        return jsonify({"error": "Invalid or expired invite link"}), 400

    if request.method == "GET":
        return jsonify({
            "email": pending.email,
            "role": pending.role,
            "name": pending.name
        }), 200

    data = request.get_json()
    password = data.get("password")

    if not password:
        return jsonify({"error": "Password is required"}), 400

    # Check if already activated
    if User.query.filter_by(email=pending.email).first():
        return jsonify({"error": "User already activated"}), 400

    # Create the user with bcrypt hashing
    user = User(
        name=pending.name,
        email=pending.email,
        role=pending.role,
        invite_token=pending.invite_token,
        is_active=True
    )
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    #  Linked profiles based on role
    role = pending.role.lower()
    if role == "doctor":
        db.session.add(Doctor(user_id=user.id, hospital_id=pending.hospital_id))
    elif role == "pharmacy":
        db.session.add(Pharmacy(user_id=user.id))
    elif role in ("labtech", "technician"):
        db.session.add(Technician(user_id=user.id))
    elif role == "hospital":
        db.session.add(Hospital(user_id=user.id))

    pending.is_accepted = True
    db.session.commit()

    token = create_access_token(
        identity=user.id,
        additional_claims={"role": user.role},
        expires_delta=timedelta(hours=2)
    )

    return jsonify({
        "message": f"Welcome {user.name}! Your {user.role} account is now active.",
        "access_token": token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    }), 201

