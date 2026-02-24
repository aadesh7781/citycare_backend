from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime
from utils.database import get_db
from utils.firebase_service import firebase_service
from middleware.auth_middleware import token_required
import os
import uuid

officer_bp = Blueprint("officer", __name__)

UPLOAD_FOLDER = "uploads/officer_proofs"


# ================= GET ALL OFFICERS =================
@officer_bp.route("/all", methods=["GET"])
@token_required
def get_all_officers(current_user):
    db = get_db()
    try:
        officers = list(db.users.find({"role": "officer"}))
        formatted = []
        for o in officers:
            formatted.append({
                "id": str(o["_id"]),
                "name": o.get("name", ""),
                "email": o.get("email", ""),
                "department": o.get("department", ""),
                "badge_number": o.get("badge_number", ""),
                "overall_rating": o.get("overall_rating", 0),
                "total_ratings": o.get("total_ratings", 0),
                "phone": o.get("phone", ""),
            })
        return jsonify({"officers": formatted}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= GET OFFICER PROFILE =================
@officer_bp.route("/profile", methods=["GET"])
@token_required
def get_officer_profile(current_user):
    db = get_db()
    try:
        officer = db.users.find_one({"_id": ObjectId(current_user["user_id"])})
        if not officer:
            return jsonify({"error": "Officer not found"}), 404

        resolved_count = db.complaints.count_documents({
            "resolved_by": str(current_user["user_id"]),
            "status": "resolved"
        })
        in_progress_count = db.complaints.count_documents({
            "assigned_officer.officer_id": str(current_user["user_id"]),
            "status": "in_progress"
        })

        return jsonify({
            "id": str(officer["_id"]),
            "name": officer.get("name", ""),
            "email": officer.get("email", ""),
            "department": officer.get("department", "General Department"),
            "badge_number": officer.get("badge_number", f"B-{str(officer['_id'])[:4].upper()}"),
            "overall_rating": officer.get("overall_rating", 0),
            "total_ratings": officer.get("total_ratings", 0),
            "phone": officer.get("phone", ""),
            "role": officer.get("role", "officer"),
            "resolved_complaints": resolved_count,
            "in_progress_complaints": in_progress_count,
            "joined_at": officer.get("created_at", datetime.utcnow()).isoformat() if officer.get("created_at") else None,
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= UPDATE OFFICER PROFILE =================
@officer_bp.route("/profile", methods=["PUT"])
@token_required
def update_officer_profile(current_user):
    db = get_db()
    try:
        data = request.get_json()
        allowed_fields = ["name", "phone", "department"]
        update_data = {f: data[f] for f in allowed_fields if f in data}

        if not update_data:
            return jsonify({"error": "No valid fields to update"}), 400

        db.users.update_one(
            {"_id": ObjectId(current_user["user_id"])},
            {"$set": update_data}
        )
        return jsonify({"message": "Profile updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= GET OFFICER ACTIVITIES =================
@officer_bp.route("/activities", methods=["GET"])
@token_required
def get_officer_activities(current_user):
    db = get_db()
    try:
        activities = list(
            db.officer_activities.find(
                {"officer_id": str(current_user["user_id"])}
            ).sort("timestamp", -1).limit(50)
        )
        formatted = [{
            "id": str(a["_id"]),
            "complaint_id": a.get("complaint_id", ""),
            "action": a.get("action", ""),
            "details": a.get("details", ""),
            "timestamp": a["timestamp"].isoformat() if a.get("timestamp") else None,
        } for a in activities]

        return jsonify({"activities": formatted}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= GET OFFICER STATS =================
@officer_bp.route("/stats", methods=["GET"])
@token_required
def get_officer_stats(current_user):
    db = get_db()
    try:
        officer_id = str(current_user["user_id"])
        officer = db.users.find_one({"_id": ObjectId(officer_id)})

        return jsonify({
            "total_resolved": db.complaints.count_documents({"resolved_by": officer_id, "status": "resolved"}),
            "total_in_progress": db.complaints.count_documents({"assigned_officer.officer_id": officer_id, "status": "in_progress"}),
            "total_pending": db.complaints.count_documents({"status": "pending"}),
            "overall_rating": officer.get("overall_rating", 0) if officer else 0,
            "total_ratings": officer.get("total_ratings", 0) if officer else 0,
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= GET ALL COMPLAINTS FOR OFFICER =================
@officer_bp.route("/complaints", methods=["GET"])
@token_required
def get_all_complaints_for_officer(current_user):
    db = get_db()
    if current_user.get("role") != "officer":
        return jsonify({"error": "Unauthorized"}), 403

    try:
        complaints = list(db.complaints.find().sort("urgency", -1))
        formatted = [{
            "id": str(c["_id"]),
            "category": c.get("category", ""),
            "description": c.get("description", ""),
            "location": c.get("location", ""),
            "status": c.get("status", "pending"),
            "urgency": c.get("urgency", 0),
            "imageUrl": c.get("image_url", ""),
            "createdAt": c["created_at"].isoformat(),
            "timeline": c.get("timeline", []),
            "assignedOfficer": c.get("assigned_officer", {})
        } for c in complaints]

        return jsonify({"complaints": formatted}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= GET COMPLAINT DETAIL =================
@officer_bp.route("/complaints/<complaint_id>", methods=["GET"])
@token_required
def get_complaint_detail(current_user, complaint_id):
    db = get_db()
    if current_user.get("role") != "officer":
        return jsonify({"error": "Unauthorized"}), 403

    try:
        complaint = db.complaints.find_one({"_id": ObjectId(complaint_id)})
        if not complaint:
            return jsonify({"error": "Complaint not found"}), 404

        user = db.users.find_one({"_id": complaint.get("user_id")})

        return jsonify({
            "id": str(complaint["_id"]),
            "category": complaint.get("category", ""),
            "description": complaint.get("description", ""),
            "location": complaint.get("location", ""),
            "status": complaint.get("status", "pending"),
            "urgency": complaint.get("urgency", 0),
            "imageUrl": complaint.get("image_url", ""),
            "proofImageUrl": complaint.get("proof_image_url", ""),
            "feedbackRating": complaint.get("feedback", {}).get("rating"),
            "feedbackComment": complaint.get("feedback", {}).get("feedback"),
            "createdAt": complaint["created_at"].isoformat(),
            "resolvedAt": complaint.get("resolved_at").isoformat() if complaint.get("resolved_at") else None,
            "timeline": complaint.get("timeline", []),
            "userName": user.get("name", "Unknown") if user else "Unknown",
            "userPhone": user.get("phone", "") if user else "",
            "assignedOfficer": complaint.get("assigned_officer", {}),
            "feedback": complaint.get("feedback", None)
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= UPDATE COMPLAINT STATUS =================
@officer_bp.route("/complaints/<complaint_id>/status", methods=["PUT"])
@token_required
def update_complaint_status(current_user, complaint_id):
    db = get_db()

    if current_user.get("role") != "officer":
        return jsonify({"error": "Unauthorized"}), 403

    status = request.form.get("status")
    if status not in ["pending", "in_progress", "resolved"]:
        return jsonify({"error": "Invalid status"}), 400

    proof_image_url = None
    if status == "resolved":
        if "image" not in request.files:
            return jsonify({"error": "Proof image required"}), 400
        file = request.files["image"]
        if file.filename == "":
            return jsonify({"error": "Invalid image"}), 400

        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        filename = f"{uuid.uuid4()}.jpg"
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        proof_image_url = f"/uploads/officer_proofs/{filename}"

    complaint = db.complaints.find_one({"_id": ObjectId(complaint_id)})
    if not complaint:
        return jsonify({"error": "Complaint not found"}), 404

    officer = db.users.find_one({"_id": ObjectId(current_user["user_id"])})
    officer_info = {
        "officer_id": str(officer["_id"]),
        "name": officer.get("name", "Unknown Officer"),
        "badge_number": officer.get("badge_number", f"B-{str(officer['_id'])[:4].upper()}"),
        "department": officer.get("department", "General Department")
    }

    update_data = {
        "status": status,
        "assigned_officer": officer_info,
        "last_updated": datetime.utcnow()
    }
    if status == "resolved":
        update_data["resolved_at"] = datetime.utcnow()
        update_data["resolved_by"] = str(current_user["user_id"])
        update_data["proof_image_url"] = proof_image_url

    db.complaints.update_one(
        {"_id": ObjectId(complaint_id)},
        {
            "$set": update_data,
            "$push": {"timeline": {
                "status": status.capitalize(),
                "date": datetime.utcnow().isoformat(),
                "done": True,
                "by": f"Officer {officer.get('name', 'Unknown')}"
            }}
        }
    )

    db.officer_activities.insert_one({
        "officer_id": str(current_user["user_id"]),
        "complaint_id": complaint_id,
        "action": status,
        "timestamp": datetime.utcnow(),
        "details": f"Changed status to {status}"
    })

    # ── SEND NOTIFICATION TO CITIZEN ──
    if status in ["in_progress", "resolved"]:
        try:
            citizen = db.users.find_one({"_id": complaint.get("user_id")})

            print(f"🔔 Notification debug:")
            print(f"   Complaint user_id : {complaint.get('user_id')}")
            print(f"   Citizen found     : {citizen is not None}")
            print(f"   Citizen name      : {citizen.get('name') if citizen else 'N/A'}")
            print(f"   Citizen email     : {citizen.get('email') if citizen else 'N/A'}")
            print(f"   Citizen FCM token : {'SET ✅' if citizen and citizen.get('fcm_token') else 'MISSING ❌'}")

            if citizen and citizen.get("fcm_token"):
                token_preview = citizen["fcm_token"][:30]
                print(f"   Token preview     : {token_preview}...")

                success = firebase_service.notify_status_update(
                    user_token=citizen["fcm_token"],
                    complaint_id=complaint_id,
                    new_status=status,
                    category=complaint.get("category", "Your")
                )
                print(f"   FCM result        : {'✅ Sent' if success else '❌ Failed'}")
            else:
                print(f"   ⚠️ Skipping — citizen has no FCM token registered")
                print(f"   This means the citizen has never logged in on a device,")
                print(f"   or logged out before the officer updated the status.")

        except Exception as e:
            print(f"⚠️ Error sending status notification: {e}")

    return jsonify({
        "message": "Status updated successfully",
        "status": status,
        "proof_image": proof_image_url,
        "assigned_officer": officer_info
    }), 200


# ================= SUBMIT FEEDBACK =================
@officer_bp.route("/complaints/<complaint_id>/feedback", methods=["POST"])
@token_required
def submit_complaint_feedback(current_user, complaint_id):
    db = get_db()
    try:
        data = request.get_json()
        rating = data.get("rating")
        feedback_text = data.get("feedback", "")

        if not rating or rating < 1 or rating > 5:
            return jsonify({"error": "Rating must be between 1 and 5"}), 400

        complaint = db.complaints.find_one({"_id": ObjectId(complaint_id)})
        if not complaint:
            return jsonify({"error": "Complaint not found"}), 404
        if complaint.get("status") != "resolved":
            return jsonify({"error": "Can only provide feedback for resolved complaints"}), 400
        if str(complaint.get("user_id")) != current_user["user_id"]:
            return jsonify({"error": "Unauthorized"}), 403
        if complaint.get("feedback"):
            return jsonify({"error": "Feedback already submitted"}), 400

        officer_id = complaint.get("resolved_by")
        if not officer_id:
            return jsonify({"error": "No officer assigned"}), 400

        officer = db.users.find_one({"_id": ObjectId(officer_id)})
        if not officer:
            return jsonify({"error": "Officer not found"}), 404

        db.complaints.update_one(
            {"_id": ObjectId(complaint_id)},
            {"$set": {"feedback": {
                "rating": rating,
                "feedback": feedback_text,
                "submitted_at": datetime.utcnow().isoformat(),
                "submitted_by": str(current_user["user_id"])
            }}}
        )

        current_rating = officer.get("overall_rating", 0)
        total_ratings = officer.get("total_ratings", 0)
        new_average = ((current_rating * total_ratings) + rating) / (total_ratings + 1)

        db.users.update_one(
            {"_id": ObjectId(officer_id)},
            {"$set": {
                "overall_rating": round(new_average, 2),
                "total_ratings": total_ratings + 1
            }}
        )

        try:
            if officer.get("fcm_token"):
                success = firebase_service.notify_feedback_received(
                    officer_token=officer["fcm_token"],
                    complaint_id=complaint_id,
                    rating=rating,
                    category=complaint.get("category", "a")
                )
                print(f"{'✅ Feedback notification sent' if success else '⚠️ Feedback notification failed'}")
            else:
                print("⚠️ Officer has no FCM token")
        except Exception as e:
            print(f"⚠️ Error sending feedback notification: {e}")

        return jsonify({
            "message": "Feedback submitted successfully",
            "rating": rating,
            "new_officer_rating": round(new_average, 2)
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ================= GET ACTIVITIES BY OFFICER ID (Public for citizens) =================
@officer_bp.route("/<officer_id>/activities", methods=["GET"])
@token_required
def get_officer_activities_by_id(current_user, officer_id):
    db = get_db()
    try:
        officer = db.users.find_one({"_id": ObjectId(officer_id), "role": "officer"})
        if not officer:
            return jsonify({"error": "Officer not found"}), 404

        resolved_count = db.complaints.count_documents({
            "resolved_by": officer_id,
            "status": "resolved"
        })

        activities = list(
            db.officer_activities.find(
                {"officer_id": officer_id}
            ).sort("timestamp", -1).limit(50)
        )

        formatted_activities = []
        for a in activities:
            # Try to get complaint location
            complaint_location = ""
            complaint_category = ""
            if a.get("complaint_id"):
                try:
                    complaint = db.complaints.find_one({"_id": ObjectId(a["complaint_id"])})
                    if complaint:
                        complaint_location = complaint.get("location", "")
                        complaint_category = complaint.get("category", "")
                except:
                    pass

            formatted_activities.append({
                "id": str(a["_id"]),
                "complaint_id": a.get("complaint_id", ""),
                "action": a.get("action", ""),
                "details": a.get("details", ""),
                "timestamp": a["timestamp"].isoformat() if a.get("timestamp") else None,
                "complaint_location": complaint_location,
                "complaint_category": complaint_category,
            })

        return jsonify({
            "officer": {
                "id": str(officer["_id"]),
                "name": officer.get("name", ""),
                "badge_number": officer.get("badge_number", ""),
                "department": officer.get("department", ""),
                "overall_rating": officer.get("overall_rating", 0),
                "total_ratings": officer.get("total_ratings", 0),
                "resolved_complaints": resolved_count,
            },
            "activities": formatted_activities
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500