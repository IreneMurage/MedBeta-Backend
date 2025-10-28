from flask import Blueprint, jsonify, request
from app.models.reviews import Review
from app.db import db
import logging

# Fixed url_prefix path
review_bp = Blueprint("review", __name__, url_prefix="/patients/<int:id>/reviews")

@review_bp.route("/", methods=["POST"])
def add_review(id):
    data = request.get_json()

    # Validation checks
    if not data:
        return jsonify({"error": "Request body cannot be empty"}), 400
    if "rating" not in data:
        return jsonify({"error": "Missing required field: rating"}), 400
    if not data.get("doctor_id") and not data.get("hospital_id"):
        return jsonify({"error": "Either doctor_id or hospital_id must be provided"}), 400

    try:
        # Create new review entry
        new_review = Review(
            patient_id=id,
            doctor_id=data.get("doctor_id"),
            hospital_id=data.get("hospital_id"),
            rating=data["rating"],
            comment=data.get("comment", "")
        )

        db.session.add(new_review)
        db.session.commit()

        # Return success response
        return jsonify({
            "message": "Review added successfully",
            "review": {
                "id": new_review.id,
                "patient_id": new_review.patient_id,
                "doctor_id": new_review.doctor_id,
                "hospital_id": new_review.hospital_id,
                "rating": new_review.rating,
                "comment": new_review.comment,
                "created_at": new_review.created_at.isoformat() if new_review.created_at else None
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error adding review: {e}")
        return jsonify({"error": "Internal server error"}), 500
