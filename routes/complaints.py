from flask import Blueprint, jsonify
from utils.database import get_db

complaints_bp = Blueprint("complaints_all", __name__)

@complaints_bp.route("/complaints/all", methods=["GET"])
def get_all_complaints():
    try:
        db = get_db()

        complaints = list(
            db.complaints.find().sort("created_at", -1)
        )

        formatted = []
        for c in complaints:
            formatted.append({
                "id": str(c["_id"]),
                "category": c.get("category", ""),
                "description": c.get("description", ""),
                "location": c.get("location", ""),
                "status": c.get("status", "pending"),
                "imageUrl": c.get("image_url"),
                "createdAt": c["created_at"].isoformat(),
                "timeline": c.get("timeline", [])
            })

        return jsonify({"complaints": formatted}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
