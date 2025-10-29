from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.db import db
from app.models import Review, Doctor, Hospital, User
from sqlalchemy.exc import OperationalError, SQLAlchemyError

review_bp = Blueprint("review_bp", __name__)

# ✅ Helper function for safe DB commits
def safe_commit():
    try:
        db.session.commit()
        return True, None
    except OperationalError as e:
        db.session.rollback()
        return False, f"Database connection lost: {str(e)}"
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, f"Database error: {str(e)}"

# ✅ POST /reviews — submit a review
@review_bp.route("/", methods=["POST"])
@jwt_required()
def submit_review():
    data = request.get_json()

    current_user_id = get_jwt_identity()
    if not current_user_id:
        return jsonify({"error": "Unauthorized user"}), 401

    try:
        reviewer = User.query.get(current_user_id)
        if not reviewer:
            return jsonify({"error": "Reviewer not found"}), 404

        rating = data.get("rating")
        comment = data.get("comment")
        doctor_id = data.get("doctor_id")
        hospital_id = data.get("hospital_id")

        if not rating or not comment:
            return jsonify({"error": "Rating and comment are required"}), 400

        review = Review(
            rating=rating,
            comment=comment,
            doctor_id=doctor_id,
            hospital_id=hospital_id,
            user_id=current_user_id,
        )

        db.session.add(review)
        success, error_msg = safe_commit()
        if not success:
            return jsonify({"error": error_msg}), 500

        return jsonify({
            "message": "Review submitted successfully",
            "review": review.to_dict()
        }), 201

    except OperationalError:
        return jsonify({"error": "Database connection error"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ GET /reviews/doctor/<doctor_id> — get reviews for a doctor
@review_bp.route("/doctor/<int:doctor_id>", methods=["GET"])
def get_doctor_reviews(doctor_id):
    try:
        doctor = Doctor.query.get(doctor_id)
        if not doctor:
            return jsonify({"error": "Doctor not found"}), 404

        reviews = Review.query.filter_by(doctor_id=doctor_id).all()
        return jsonify([review.to_dict() for review in reviews]), 200

    except OperationalError:
        return jsonify({"error": "Database connection lost. Please retry."}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ GET /reviews/hospital/<hospital_id> — get reviews for a hospital
@review_bp.route("/hospital/<int:hospital_id>", methods=["GET"])
def get_hospital_reviews(hospital_id):
    try:
        hospital = Hospital.query.get(hospital_id)
        if not hospital:
            return jsonify({"error": "Hospital not found"}), 404

        reviews = Review.query.filter_by(hospital_id=hospital_id).all()
        return jsonify([review.to_dict() for review in reviews]), 200

    except OperationalError:
        return jsonify({"error": "Database connection lost. Please retry."}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
