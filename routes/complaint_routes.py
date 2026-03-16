from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime
from utils.database import get_db
from utils.ml_model import predict_score             # ✅ ML Model
from utils.image_analyzer import analyze_complaint_image  # ✅ Gemini Vision
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
        category    = request.form.get("category")
        description = request.form.get("description")
        location    = request.form.get("location")
        latitude    = request.form.get("latitude")
        longitude   = request.form.get("longitude")

        if not all([category, description, location]):
            return jsonify({"error": "Missing required fields"}), 400

        image_url = None

        # ✅ CLOUDINARY IMAGE UPLOAD
        if "image" in request.files:
            file = request.files["image"]
            if file.filename != "":
                result = cloudinary.uploader.upload(
                    file,
                    folder="citycare_complaints"
                )
                image_url = result.get("secure_url")

        # ✅ ML MODEL — text se urgency score
        text_score   = predict_score(description)

        # ✅ GEMINI VISION — image se boost (agar image hai)
        image_boost  = 0
        image_note   = ""
        if image_url:
            image_result = analyze_complaint_image(image_url)
            image_boost  = image_result["boost"]
            image_note   = image_result["analysis"]


        urgency = max(0, min(100, text_score + image_boost))

        print(f"📊 Text={text_score} + Image={image_boost} → Final={urgency}")

        complaint = {
            "user_id"    : ObjectId(current_user["user_id"]),
            "category"   : category,
            "description": description,
            "location"   : location,
            "latitude"   : float(latitude) if latitude else None,
            "longitude"  : float(longitude) if longitude else None,
            "image_url"  : image_url,
            "status"     : "pending",
            "urgency"    : urgency,
            "created_at" : datetime.utcnow(),
            "timeline"   : [
                {
                    "status": "Submitted",
                    "date"  : datetime.utcnow().isoformat(),
                    "done"  : True,
                    "by"    : "User"
                }
            ]
        }

        result       = db.complaints.insert_one(complaint)
        complaint_id = str(result.inserted_id)

        # ── AUTO-ASSIGN officer by department ──────────────────────
        CATEGORY_DEPT = {
            "roads": "roads", "road": "roads", "pothole": "roads",
            "water": "water",
            "drainage": "drainage", "flood": "drainage",
            "electricity": "electricity", "power": "electricity", "streetlight": "electricity",
            "sanitation": "sanitation", "garbage": "sanitation", "waste": "sanitation",
            "safety": "safety", "crime": "safety",
            "environment": "environment", "pollution": "environment",
            "health": "health",
            "infrastructure": "infrastructure",
            "transport": "transport",
        }

        dept = CATEGORY_DEPT.get(category.lower().strip(), None)
        assigned_officer_info = None

        if dept:
            dept_officers = list(db.users.find({"role": "officer", "department": dept}))
            if dept_officers:
                def officer_load(o):
                    return db.complaints.count_documents({
                        "assigned_officer.officer_id": str(o["_id"]),
                        "status": {"$in": ["pending", "in_progress"]}
                    })
                best_officer = min(dept_officers, key=officer_load)
                assigned_officer_info = {
                    "officer_id"  : str(best_officer["_id"]),
                    "name"        : best_officer.get("name", ""),
                    "badge_number": best_officer.get("badge_number", ""),
                    "department"  : best_officer.get("department", ""),
                }
                db.complaints.update_one(
                    {"_id": result.inserted_id},
                    {"$set": {"assigned_officer": assigned_officer_info, "status": "in_progress"},
                     "$push": {"timeline": {"status": "Assigned", "date": datetime.utcnow().isoformat(), "done": True, "by": f"Auto → {best_officer.get('name', '')}"}}}
                )

        # 🔥 NOTIFY OFFICERS
        try:
            if assigned_officer_info:
                assigned_doc = db.users.find_one({"_id": ObjectId(assigned_officer_info["officer_id"])})
                if assigned_doc and assigned_doc.get("fcm_token"):
                    firebase_service.notify_new_complaint(
                        officer_tokens=[assigned_doc["fcm_token"]],
                        complaint_id=complaint_id, category=category,
                        location=location, urgency=urgency
                    )
            else:
                officers = list(db.users.find(
                    {"role": "officer", "fcm_token": {"$exists": True, "$ne": None}},
                    {"fcm_token": 1}
                ))
                officer_tokens = [o["fcm_token"] for o in officers]
                if officer_tokens:
                    firebase_service.notify_new_complaint(
                        officer_tokens=officer_tokens,
                        complaint_id=complaint_id, category=category,
                        location=location, urgency=urgency
                    )
        except Exception as e:
            print(f"Notification error: {e}")

        return jsonify({
            "message"          : "Complaint submitted successfully",
            "complaint_id"     : complaint_id,
            "urgency"          : urgency,
            "assigned_officer" : assigned_officer_info,
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

        assigned = complaint.get("assigned_officer", {})

        formatted = {
            "id"                  : str(complaint["_id"]),
            "category"            : complaint.get("category", ""),
            "description"         : complaint.get("description", ""),
            "location"            : complaint.get("location", ""),
            "status"              : complaint.get("status", "pending"),
            "urgency"             : complaint.get("urgency", 0),
            "imageUrl"            : complaint.get("image_url", ""),
            "proofImageUrl"       : complaint.get("proof_image_url", ""),
            "feedbackRating"      : complaint.get("feedback_rating"),
            "feedbackComment"     : complaint.get("feedback_comment"),
            "createdAt"           : complaint["created_at"].isoformat(),
            "resolvedAt"          : complaint.get("resolved_at").isoformat() if complaint.get("resolved_at") else None,
            "timeline"            : complaint.get("timeline", []),
            "assignedOfficer"     : assigned if assigned else None,
            "resolutionConfirmed" : complaint.get("resolution_confirmed", False),
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
            assigned = c.get("assigned_officer", {})
            formatted.append({
                "id"                  : str(c["_id"]),
                "category"            : c.get("category", ""),
                "description"         : c.get("description", ""),
                "location"            : c.get("location", ""),
                "status"              : c.get("status", "pending"),
                "urgency"             : c.get("urgency", 0),
                "imageUrl"            : c.get("image_url", ""),
                "proofImageUrl"       : c.get("proof_image_url", ""),
                "feedbackRating"      : c.get("feedback_rating"),
                "feedbackComment"     : c.get("feedback_comment"),
                "createdAt"           : c["created_at"].isoformat(),
                "resolvedAt"          : c.get("resolved_at").isoformat() if c.get("resolved_at") else None,
                "timeline"            : c.get("timeline", []),
                "assignedOfficer"     : assigned if assigned else None,
                "resolutionConfirmed" : c.get("resolution_confirmed", False),
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
            assigned = c.get("assigned_officer", {})
            formatted.append({
                "id"                  : str(c["_id"]),
                "category"            : c.get("category", ""),
                "description"         : c.get("description", ""),
                "location"            : c.get("location", ""),
                "status"              : c.get("status", "pending"),
                "urgency"             : c.get("urgency", 0),
                "imageUrl"            : c.get("image_url", ""),
                "proofImageUrl"       : c.get("proof_image_url", ""),
                "feedbackRating"      : c.get("feedback_rating"),
                "feedbackComment"     : c.get("feedback_comment"),
                "createdAt"           : c["created_at"].isoformat(),
                "resolvedAt"          : c.get("resolved_at").isoformat() if c.get("resolved_at") else None,
                "timeline"            : c.get("timeline", []),
                "assignedOfficer"     : assigned if assigned else None,
                "resolutionConfirmed" : c.get("resolution_confirmed", False),
            })

        return jsonify({"complaints": formatted}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500




@complaint_bp.route("/<complaint_id>/confirm-resolution", methods=["POST"])
@token_required
def confirm_resolution(current_user, complaint_id):
    """
    User confirms OR rejects officer's resolution proof.
    action = "confirm" → complaint closed
    action = "reject"  → complaint reopened, officer notified
    """
    db   = get_db()
    data = request.get_json() or {}

    action = data.get("action")  # "confirm" or "reject"
    reason = data.get("reason", "")

    if action not in ["confirm", "reject"]:
        return jsonify({"error": "action must be confirm or reject"}), 400

    try:
        complaint = db.complaints.find_one({"_id": ObjectId(complaint_id)})
        if not complaint:
            return jsonify({"error": "Complaint not found"}), 404

        # Only the complaint owner can confirm
        if str(complaint.get("user_id")) != current_user["user_id"]:
            return jsonify({"error": "Unauthorized"}), 403

        # Must be in resolved state with proof
        if complaint.get("status") != "resolved":
            return jsonify({"error": "Complaint is not in resolved state"}), 400

        if not complaint.get("proof_image_url"):
            return jsonify({"error": "No proof image uploaded by officer"}), 400

        now = datetime.utcnow()

        if action == "confirm":
            db.complaints.update_one(
                {"_id": ObjectId(complaint_id)},
                {"$set": {
                    "resolution_confirmed"    : True,
                    "resolution_confirmed_by" : current_user["user_id"],
                    "resolution_confirmed_at" : now,
                    "status"                  : "closed",
                },
                    "$push": {"timeline": {
                        "status": "Closed",
                        "date"  : now.isoformat(),
                        "done"  : True,
                        "by"    : "Citizen Confirmed"
                    }}}
            )
            return jsonify({"message": "Resolution confirmed. Complaint closed. ✅"}), 200

        else:  # reject
            reopen_count = complaint.get("reopened_count", 0) + 1

            db.complaints.update_one(
                {"_id": ObjectId(complaint_id)},
                {"$set": {
                    "status"         : "in_progress",
                    "proof_image_url": None,
                    "reopened_count" : reopen_count,
                    "reopened_reason": reason,
                    "reopened_at"    : now,
                },
                    "$push": {"timeline": {
                        "status": "Reopened",
                        "date"  : now.isoformat(),
                        "done"  : True,
                        "by"    : f"Citizen Rejected: {reason}"
                    }}}
            )

            # Notify officer
            try:
                assigned = complaint.get("assigned_officer", {})
                if assigned.get("officer_id"):
                    officer = db.users.find_one({"_id": ObjectId(assigned["officer_id"])})
                    if officer and officer.get("fcm_token"):
                        from utils.firebase_service import firebase_service
                        firebase_service.send_notification(
                            token  = officer["fcm_token"],
                            title  = "Resolution Rejected ❌",
                            body   = f"Citizen rejected your resolution. Reason: {reason or 'Not specified'}",
                            data   = {"complaint_id": complaint_id, "type": "resolution_rejected"}
                        )
            except Exception as e:
                print(f"Notification error: {e}")

            return jsonify({"message": "Resolution rejected. Complaint reopened.", "reopen_count": reopen_count}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500




@complaint_bp.route("/auto-confirm-resolutions", methods=["POST"])
@token_required
def auto_confirm_resolutions(current_user):
    if current_user.get("role") != "admin":
        return jsonify({"error": "Admin only"}), 403

    db  = get_db()
    now = datetime.utcnow()

    from datetime import timedelta
    cutoff = now - timedelta(hours=48)

    pending = list(db.complaints.find({
        "status"              : "resolved",
        "proof_image_url"     : {"$ne": None},
        "resolution_confirmed": {"$ne": True},
        "resolved_at"         : {"$lt": cutoff}
    }))

    count = 0
    for c in pending:
        db.complaints.update_one(
            {"_id": c["_id"]},
            {"$set": {
                "resolution_confirmed"   : True,
                "resolution_confirmed_by": "auto",
                "resolution_confirmed_at": now,
                "status"                 : "closed",
            },
                "$push": {"timeline": {
                    "status": "Auto-Closed",
                    "date"  : now.isoformat(),
                    "done"  : True,
                    "by"    : "System (48hr auto-confirm)"
                }}}
        )
        count += 1

    return jsonify({"message": f"Auto-confirmed {count} complaints"}), 200