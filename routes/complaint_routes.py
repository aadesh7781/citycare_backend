from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime
from utils.database import get_db
from utils.urgency_engine import calculate_urgency
from utils.firebase_service import firebase_service
from middleware.auth_middleware import token_required
import cloudinary.uploader
import os

complaint_bp = Blueprint("complaint", __name__)

@complaint_bp.route("/submit", methods=["POST"])
@token_required
def submit_complaint(current_user):
    db = get_db()

    try:
        category = request.form.get("category")
        description = request.form.get("description")
        location = request.form.get("location")
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")

        if not all([category, description, location]):
            return jsonify({"error": "Missing required fields"}), 400

        image_url = None
        image_path = None

        # ✅ CLOUDINARY IMAGE UPLOAD
        if "image" in request.files:
            file = request.files["image"]
            if file.filename != "":
                result = cloudinary.uploader.upload(
                    file,
                    folder="citycare_complaints"
                )
                image_url = result.get("secure_url")
                image_path = None  # No local file now

        # Urgency calculation (without local image path now)
        urgency = calculate_urgency(
            description=description,
            category=category,
            image_path=image_path
        )

        complaint = {
            "user_id": ObjectId(current_user["user_id"]),
            "category": category,
            "description": description,
            "location": location,
            "latitude": float(latitude) if latitude else None,
            "longitude": float(longitude) if longitude else None,
            "image_url": image_url,
            "status": "pending",
            "urgency": urgency,
            "created_at": datetime.utcnow(),
            "timeline": [
                {
                    "status": "Submitted",
                    "date": datetime.utcnow().isoformat(),
                    "done": True,
                    "by": "User"
                }
            ]
        }

        result = db.complaints.insert_one(complaint)
        complaint_id = str(result.inserted_id)

        # 🔥 NOTIFY OFFICERS
        try:
            officers = list(db.users.find(
                {"role": "officer", "fcm_token": {"$exists": True, "$ne": None}},
                {"fcm_token": 1}
            ))

            officer_tokens = [o["fcm_token"] for o in officers]

            if officer_tokens:
                firebase_service.notify_new_complaint(
                    officer_tokens=officer_tokens,
                    complaint_id=complaint_id,
                    category=category,
                    location=location,
                    urgency=urgency
                )

        except Exception as e:
            print(f"Notification error: {e}")

        return jsonify({
            "message": "Complaint submitted successfully",
            "complaint_id": complaint_id,
            "urgency": urgency
        }), 201

    except Exception as e:
        print(f"Submit error: {e}")
        return jsonify({"error": str(e)}), 500


@complaint_bp.route("/<complaint_id>", methods=["GET"])
@token_required
def get_complaint(current_user, complaint_id):
    db = get_db()

    try:
        complaint = db.complaints.find_one({"_id": ObjectId(complaint_id)})

        if not complaint:
            return jsonify({"error": "Complaint not found"}), 404

        if (str(complaint.get("user_id")) != current_user["user_id"] and
                current_user.get("role") != "officer"):
            return jsonify({"error": "Unauthorized"}), 403

        formatted = {
            "id": str(complaint["_id"]),
            "category": complaint.get("category", ""),
            "description": complaint.get("description", ""),
            "location": complaint.get("location", ""),
            "status": complaint.get("status", "pending"),
            "urgency": complaint.get("urgency", 0),
            "imageUrl": complaint.get("image_url", ""),
            "proofImageUrl": complaint.get("proof_image_url", ""),
            "feedbackRating": complaint.get("feedback_rating"),
            "feedbackComment": complaint.get("feedback_comment"),
            "createdAt": complaint["created_at"].isoformat(),
            "resolvedAt": complaint.get("resolved_at").isoformat() if complaint.get("resolved_at") else None,
            "timeline": complaint.get("timeline", [])
        }

        return jsonify(formatted), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@complaint_bp.route("/my-complaints", methods=["GET"])
@token_required
def get_my_complaints(current_user):
    db = get_db()

    try:
        complaints = list(
            db.complaints.find({"user_id": ObjectId(current_user["user_id"])})
            .sort("created_at", -1)
        )

        formatted = []
        for c in complaints:
            formatted.append({
                "id": str(c["_id"]),
                "category": c.get("category", ""),
                "description": c.get("description", ""),
                "location": c.get("location", ""),
                "status": c.get("status", "pending"),
                "urgency": c.get("urgency", 0),
                "imageUrl": c.get("image_url", ""),
                "proofImageUrl": c.get("proof_image_url", ""),
                "feedbackRating": c.get("feedback_rating"),
                "feedbackComment": c.get("feedback_comment"),
                "createdAt": c["created_at"].isoformat(),
                "resolvedAt": c.get("resolved_at").isoformat() if c.get("resolved_at") else None,
                "timeline": c.get("timeline", [])
            })

        return jsonify({"complaints": formatted}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@complaint_bp.route("/all", methods=["GET"])
@token_required
def get_all_complaints(current_user):
    db = get_db()

    if current_user.get("role") not in ["officer", "admin"]:
        return jsonify({"error": "Unauthorized"}), 403

    try:
        complaints = list(db.complaints.find().sort("urgency", -1))

        formatted = []
        for c in complaints:
            formatted.append({
                "id": str(c["_id"]),
                "category": c.get("category", ""),
                "description": c.get("description", ""),
                "location": c.get("location", ""),
                "status": c.get("status", "pending"),
                "urgency": c.get("urgency", 0),
                "imageUrl": c.get("image_url", ""),
                "proofImageUrl": c.get("proof_image_url", ""),
                "feedbackRating": c.get("feedback_rating"),
                "feedbackComment": c.get("feedback_comment"),
                "createdAt": c["created_at"].isoformat(),
                "resolvedAt": c.get("resolved_at").isoformat() if c.get("resolved_at") else None,
                "timeline": c.get("timeline", [])
            })

        return jsonify({"complaints": formatted}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500