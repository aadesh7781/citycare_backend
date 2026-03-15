# routes/admin_routes.py

from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime
import bcrypt
from utils.database import get_db
from middleware.auth_middleware import token_required
import cloudinary.uploader

admin_bp = Blueprint("admin", __name__)


# ── Admin Guard ───────────────────────────────────────────────────
def admin_required(f):
    from functools import wraps
    @wraps(f)
    @token_required
    def decorated(current_user, *args, **kwargs):
        if current_user.get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return f(current_user, *args, **kwargs)
    return decorated


# ═══════════════════════════════════════════════════════
#  DASHBOARD STATS
# ═══════════════════════════════════════════════════════

@admin_bp.route("/dashboard", methods=["GET"])
@token_required
def dashboard(current_user):
    if current_user.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403
    db = get_db()
    try:
        return jsonify({
            "total_users"       : db.users.count_documents({"role": "citizen"}),
            "pending_verif"     : db.users.count_documents({"role": "citizen", "verification_status": "pending"}),
            "total_officers"    : db.users.count_documents({"role": "officer"}),
            "total_complaints"  : db.complaints.count_documents({}),
            "pending_complaints": db.complaints.count_documents({"status": "pending"}),
            "resolved_complaints": db.complaints.count_documents({"status": "resolved"}),
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ═══════════════════════════════════════════════════════
#  OFFICER MANAGEMENT
# ═══════════════════════════════════════════════════════

@admin_bp.route("/officers", methods=["GET"])
@token_required
def get_officers(current_user):
    if current_user.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403
    db = get_db()
    try:
        officers = list(db.users.find({"role": "officer"}))
        result = []
        for o in officers:
            resolved = db.complaints.count_documents({"resolved_by": str(o["_id"]), "status": "resolved"})
            in_prog  = db.complaints.count_documents({"assigned_officer.officer_id": str(o["_id"]), "status": "in_progress"})
            result.append({
                "id"              : str(o["_id"]),
                "name"            : o.get("name", ""),
                "email"           : o.get("email", ""),
                "phone"           : o.get("phone", ""),
                "department"      : o.get("department", ""),
                "badge_number"    : o.get("badge_number", ""),
                "overall_rating"  : o.get("overall_rating", 0),
                "total_ratings"   : o.get("total_ratings", 0),
                "resolved_count"  : resolved,
                "inprogress_count": in_prog,
                "created_at"      : o.get("created_at", datetime.utcnow()).isoformat(),
            })
        return jsonify({"officers": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/officers", methods=["POST"])
@token_required
def create_officer(current_user):
    if current_user.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403
    db   = get_db()
    data = request.get_json()

    required = ["name", "email", "phone", "password", "department"]
    for f in required:
        if not data.get(f):
            return jsonify({"error": f"{f} is required"}), 400

    if db.users.find_one({"email": data["email"]}):
        return jsonify({"error": "Email already registered"}), 400

    departments = ["roads", "water", "electricity", "drainage", "sanitation", "safety", "environment", "health", "infrastructure", "transport"]
    if data["department"].lower() not in departments:
        return jsonify({"error": f"Invalid department. Choose from: {', '.join(departments)}"}), 400

    hashed = bcrypt.hashpw(data["password"].encode("utf-8"), bcrypt.gensalt())

    # Auto badge number
    count        = db.users.count_documents({"role": "officer"}) + 1
    badge_number = f"CC-{data['department'][:3].upper()}-{count:03d}"

    officer = {
        "name"        : data["name"],
        "email"       : data["email"],
        "phone"       : data["phone"],
        "password"    : hashed,
        "role"        : "officer",
        "department"  : data["department"].lower(),
        "badge_number": badge_number,
        "overall_rating": 0,
        "total_ratings" : 0,
        "created_by"  : str(current_user["user_id"]),
        "created_at"  : datetime.utcnow(),
    }

    result = db.users.insert_one(officer)
    return jsonify({
        "message"     : "Officer created successfully",
        "officer_id"  : str(result.inserted_id),
        "badge_number": badge_number,
    }), 201


@admin_bp.route("/officers/<officer_id>", methods=["DELETE"])
@token_required
def delete_officer(current_user, officer_id):
    if current_user.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403
    db = get_db()
    try:
        officer = db.users.find_one({"_id": ObjectId(officer_id), "role": "officer"})
        if not officer:
            return jsonify({"error": "Officer not found"}), 404

        db.users.delete_one({"_id": ObjectId(officer_id)})
        return jsonify({"message": "Officer removed successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ═══════════════════════════════════════════════════════
#  USER VERIFICATION
# ═══════════════════════════════════════════════════════

@admin_bp.route("/users", methods=["GET"])
@token_required
def get_users(current_user):
    if current_user.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403
    db = get_db()
    try:
        status = request.args.get("status")  # pending / approved / rejected / all
        query  = {"role": "citizen"}
        if status and status != "all":
            query["verification_status"] = status

        users = list(db.users.find(query).sort("created_at", -1))
        result = []
        for u in users:
            result.append({
                "id"                  : str(u["_id"]),
                "name"                : u.get("name", ""),
                "email"               : u.get("email", ""),
                "phone"               : u.get("phone", ""),
                "verification_status" : u.get("verification_status", "pending"),
                "verification_document": u.get("verification_document", ""),
                "verification_note"   : u.get("verification_note", ""),
                "is_banned"           : u.get("is_banned", False),
                "created_at"          : u.get("created_at", datetime.utcnow()).isoformat(),
                "complaints_count"    : db.complaints.count_documents({"user_id": u["_id"]}),
            })
        return jsonify({"users": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/users/<user_id>/verify", methods=["PUT"])
@token_required
def verify_user(current_user, user_id):
    if current_user.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403
    db   = get_db()
    data = request.get_json()

    action = data.get("action")  # approve / reject
    note   = data.get("note", "")

    if action not in ["approve", "reject"]:
        return jsonify({"error": "Action must be approve or reject"}), 400

    user = db.users.find_one({"_id": ObjectId(user_id), "role": "citizen"})
    if not user:
        return jsonify({"error": "User not found"}), 404

    status = "approved" if action == "approve" else "rejected"

    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "verification_status": status,
            "verification_note"  : note,
            "verified_by"        : str(current_user["user_id"]),
            "verified_at"        : datetime.utcnow(),
        }}
    )

    return jsonify({"message": f"User {status} successfully"}), 200


@admin_bp.route("/users/<user_id>/ban", methods=["PUT"])
@token_required
def ban_user(current_user, user_id):
    if current_user.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403
    db   = get_db()
    data = request.get_json()

    action = data.get("action")  # ban / unban
    if action not in ["ban", "unban"]:
        return jsonify({"error": "Action must be ban or unban"}), 400

    user = db.users.find_one({"_id": ObjectId(user_id), "role": "citizen"})
    if not user:
        return jsonify({"error": "User not found"}), 404

    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_banned": action == "ban"}}
    )

    return jsonify({"message": f"User {action}ned successfully"}), 200


# ═══════════════════════════════════════════════════════
#  COMPLAINT MANAGEMENT
# ═══════════════════════════════════════════════════════

@admin_bp.route("/complaints", methods=["GET"])
@token_required
def get_complaints(current_user):
    if current_user.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403
    db = get_db()
    try:
        complaints = list(db.complaints.find().sort("urgency", -1))
        result = []
        for c in complaints:
            user = db.users.find_one({"_id": c.get("user_id")})
            result.append({
                "id"                  : str(c["_id"]),
                "category"            : c.get("category", ""),
                "description"         : c.get("description", ""),
                "location"            : c.get("location", ""),
                "status"              : c.get("status", "pending"),
                "urgency"             : c.get("urgency", 0),
                "imageUrl"            : c.get("image_url", ""),
                "proofImageUrl"       : c.get("proof_image_url", ""),
                "assignedOfficer"     : c.get("assigned_officer", {}),
                "timeline"            : c.get("timeline", []),
                "createdAt"           : c["created_at"].isoformat(),
                "resolvedAt"          : c.get("resolved_at").isoformat() if c.get("resolved_at") else None,
                "resolutionConfirmed" : c.get("resolution_confirmed", False),
                "userName"            : user.get("name", "Unknown") if user else "Unknown",
                "userPhone"           : user.get("phone", "") if user else "",
                "feedbackRating"      : c.get("feedback_rating"),
                "feedbackComment"     : c.get("feedback_comment"),
            })
        return jsonify({"complaints": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/complaints/<complaint_id>/assign", methods=["PUT"])
@token_required
def assign_complaint(current_user, complaint_id):
    if current_user.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403
    db   = get_db()
    data = request.get_json()

    officer_id = data.get("officer_id")
    if not officer_id:
        return jsonify({"error": "officer_id is required"}), 400

    officer = db.users.find_one({"_id": ObjectId(officer_id), "role": "officer"})
    if not officer:
        return jsonify({"error": "Officer not found"}), 404

    complaint = db.complaints.find_one({"_id": ObjectId(complaint_id)})
    if not complaint:
        return jsonify({"error": "Complaint not found"}), 404

    officer_info = {
        "officer_id"  : str(officer["_id"]),
        "name"        : officer.get("name", ""),
        "badge_number": officer.get("badge_number", ""),
        "department"  : officer.get("department", ""),
    }

    db.complaints.update_one(
        {"_id": ObjectId(complaint_id)},
        {
            "$set" : {"assigned_officer": officer_info, "status": "in_progress"},
            "$push": {"timeline": {
                "status": "Assigned",
                "date"  : datetime.utcnow().isoformat(),
                "done"  : True,
                "by"    : f"Admin → {officer.get('name', '')}"
            }}
        }
    )

    # Notify officer
    try:
        from utils.firebase_service import firebase_service
        if officer.get("fcm_token"):
            firebase_service.notify_new_complaint(
                officer_tokens=[officer["fcm_token"]],
                complaint_id=complaint_id,
                category=complaint.get("category", ""),
                location=complaint.get("location", ""),
                urgency=complaint.get("urgency", 0)
            )
    except Exception as e:
        print(f"Notification error: {e}")

    return jsonify({
        "message"         : "Complaint assigned successfully",
        "assigned_officer": officer_info,
    }), 200