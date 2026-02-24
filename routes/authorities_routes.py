from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime
from utils.database import get_db
from middleware.auth_middleware import token_required

authorities_bp = Blueprint("authorities", __name__)


@authorities_bp.route("/", methods=["GET"])
def get_all_authorities():
    """Get all civic authorities (public endpoint - no auth required)"""
    db = get_db()

    try:
        # Fetch all officers/authorities from users collection
        authorities = list(
            db.users.find({"role": "officer"}).sort("name", 1)
        )

        formatted = []
        for auth in authorities:
            # Get statistics for each officer
            total_complaints = db.complaints.count_documents({})
            resolved_complaints = db.complaints.count_documents({"status": "resolved"})

            formatted.append({
                "id": str(auth["_id"]),
                "name": auth.get("name", "Unknown Officer"),
                "designation": auth.get("designation", auth.get("department", "Municipal Officer")),
                "department": auth.get("department", "General Department"),
                "ward": auth.get("ward", "All Wards"),
                "phone": auth.get("phone", ""),
                "email": auth.get("email", ""),
                "badgeNumber": auth.get("badge_number", f"B-{str(auth['_id'])[:4].upper()}"),
                "officerId": auth.get("officer_id", f"OFF-{str(auth['_id'])[:4]}"),
                "avatar": auth.get("avatar", "👨‍💼"),
                "statistics": {
                    "totalComplaints": total_complaints,
                    "resolvedComplaints": resolved_complaints,
                    "activeComplaints": total_complaints - resolved_complaints
                },
                "availability": auth.get("availability", "Available"),
                "joinDate": auth.get("created_at").strftime("%B %Y") if auth.get("created_at") else "N/A"
            })

        return jsonify({"authorities": formatted}), 200

    except Exception as e:
        print(f"❌ Error fetching authorities: {str(e)}")
        return jsonify({"error": str(e)}), 500


@authorities_bp.route("/<authority_id>", methods=["GET"])
def get_authority_detail(authority_id):
    """Get detailed information about a specific authority (public endpoint)"""
    db = get_db()

    try:
        authority = db.users.find_one({"_id": ObjectId(authority_id), "role": "officer"})

        if not authority:
            return jsonify({"error": "Authority not found"}), 404

        # Get statistics
        total_complaints = db.complaints.count_documents({})
        resolved_complaints = db.complaints.count_documents({"status": "resolved"})
        in_progress = db.complaints.count_documents({"status": "in_progress"})
        pending = db.complaints.count_documents({"status": "pending"})

        formatted = {
            "id": str(authority["_id"]),
            "name": authority.get("name", "Unknown Officer"),
            "designation": authority.get("designation", authority.get("department", "Municipal Officer")),
            "department": authority.get("department", "General Department"),
            "ward": authority.get("ward", "All Wards"),
            "phone": authority.get("phone", ""),
            "email": authority.get("email", ""),
            "badgeNumber": authority.get("badge_number", f"B-{str(authority['_id'])[:4].upper()}"),
            "officerId": authority.get("officer_id", f"OFF-{str(authority['_id'])[:4]}"),
            "avatar": authority.get("avatar", "👨‍💼"),
            "bio": authority.get("bio", "Dedicated civic officer committed to serving the community."),
            "statistics": {
                "totalComplaints": total_complaints,
                "resolvedComplaints": resolved_complaints,
                "inProgress": in_progress,
                "pending": pending,
                "resolutionRate": round((resolved_complaints / total_complaints * 100), 1) if total_complaints > 0 else 0
            },
            "availability": authority.get("availability", "Available"),
            "workingHours": authority.get("working_hours", "Mon-Fri: 9:00 AM - 6:00 PM"),
            "joinDate": authority.get("created_at").strftime("%B %d, %Y") if authority.get("created_at") else "N/A"
        }

        return jsonify(formatted), 200

    except Exception as e:
        print(f"❌ Error fetching authority detail: {str(e)}")
        return jsonify({"error": str(e)}), 500


@authorities_bp.route("/departments", methods=["GET"])
def get_departments():
    """Get list of all departments with authority counts"""
    db = get_db()

    try:
        # Aggregate by department
        pipeline = [
            {"$match": {"role": "officer"}},
            {"$group": {
                "_id": "$department",
                "count": {"$sum": 1},
                "officers": {"$push": {
                    "name": "$name",
                    "phone": "$phone"
                }}
            }},
            {"$sort": {"_id": 1}}
        ]

        departments = list(db.users.aggregate(pipeline))

        formatted = []
        for dept in departments:
            formatted.append({
                "department": dept["_id"] if dept["_id"] else "General Department",
                "officerCount": dept["count"],
                "officers": dept["officers"]
            })

        return jsonify({"departments": formatted}), 200

    except Exception as e:
        print(f"❌ Error fetching departments: {str(e)}")
        return jsonify({"error": str(e)}), 500


@authorities_bp.route("/search", methods=["GET"])
def search_authorities():
    """Search authorities by name, department, or ward"""
    db = get_db()

    try:
        query = request.args.get('q', '')
        department = request.args.get('department', None)
        ward = request.args.get('ward', None)

        # Build search query
        search_filter = {"role": "officer"}

        if query:
            search_filter["$or"] = [
                {"name": {"$regex": query, "$options": "i"}},
                {"department": {"$regex": query, "$options": "i"}},
                {"designation": {"$regex": query, "$options": "i"}}
            ]

        if department:
            search_filter["department"] = department

        if ward:
            search_filter["ward"] = ward

        authorities = list(db.users.find(search_filter).sort("name", 1))

        formatted = []
        for auth in authorities:
            formatted.append({
                "id": str(auth["_id"]),
                "name": auth.get("name", "Unknown Officer"),
                "designation": auth.get("designation", auth.get("department", "Municipal Officer")),
                "department": auth.get("department", "General Department"),
                "ward": auth.get("ward", "All Wards"),
                "phone": auth.get("phone", ""),
                "email": auth.get("email", ""),
                "avatar": auth.get("avatar", "👨‍💼")
            })

        return jsonify({
            "authorities": formatted,
            "count": len(formatted),
            "query": query
        }), 200

    except Exception as e:
        print(f"❌ Error searching authorities: {str(e)}")
        return jsonify({"error": str(e)}), 500