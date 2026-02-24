from flask import Blueprint, jsonify
from utils.database import get_db
from datetime import datetime, timezone

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/home-stats", methods=["GET"])
def home_stats():
    """
    Lightweight stats for the Home Screen quick-overview cards.

    Returns:
      - today_complaints  : complaints submitted today
      - today_resolved    : complaints resolved today
      - resolution_rate   : % of all-time complaints that are resolved (rounded int)
    """
    db = get_db()

    # ── today boundaries (UTC) ──────────────────────────────────────────────
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Today's submitted complaints
    today_complaints = db.complaints.count_documents({
        "created_at": {"$gte": today_start}
    })

    # Today's resolved: submitted today AND resolved today
    today_resolved = db.complaints.count_documents({
        "status": "resolved",
        "created_at": {"$gte": today_start},
        "resolved_at": {"$gte": today_start}
    })

    # Today's pending complaints
    today_pending = db.complaints.count_documents({
        "status": "pending",
        "created_at": {"$gte": today_start}
    })

    return jsonify({
        "today_complaints": today_complaints,
        "today_resolved": today_resolved,
        "today_pending": today_pending,
    })


@analytics_bp.route("/summary", methods=["GET"])
def analytics_summary():
    db = get_db()

    total = db.complaints.count_documents({})

    pending = db.complaints.count_documents({"status": "pending"})
    in_progress = db.complaints.count_documents({"status": "in_progress"})
    resolved = db.complaints.count_documents({"status": "resolved"})
    rejected = db.complaints.count_documents({"status": "rejected"})

    # Calculate average resolution time
    avg_resolution_time = "N/A"
    resolved_complaints = list(db.complaints.find({
        "status": "resolved",
        "resolved_at": {"$exists": True},
        "created_at": {"$exists": True}
    }))

    if resolved_complaints:
        total_time_hours = 0
        count = 0

        for complaint in resolved_complaints:
            created_at = complaint.get("created_at")
            resolved_at = complaint.get("resolved_at")

            if created_at and resolved_at:
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                if isinstance(resolved_at, str):
                    resolved_at = datetime.fromisoformat(resolved_at.replace('Z', '+00:00'))

                time_diff = resolved_at - created_at
                total_time_hours += time_diff.total_seconds() / 3600
                count += 1

        if count > 0:
            avg_hours = total_time_hours / count

            if avg_hours < 1:
                avg_resolution_time = f"{int(avg_hours * 60)} mins"
            elif avg_hours < 24:
                avg_resolution_time = f"{avg_hours:.1f} hrs"
            else:
                days = avg_hours / 24
                avg_resolution_time = f"{days:.1f} days"

    # Authority-wise grouping
    pipeline = [
        {
            "$group": {
                "_id": "$category",
                "count": {"$sum": 1}
            }
        }
    ]

    authority_data = list(db.complaints.aggregate(pipeline))

    authorities = [
        {
            "authority": a["_id"],
            "count": a["count"]
        }
        for a in authority_data
    ]

    # Locations for map
    locations = []
    for c in db.complaints.find({}, {"location": 1, "category": 1, "status": 1}):
        if "," in c.get("location", ""):
            lat, lng = c["location"].split(",")
            locations.append({
                "lat": float(lat.strip()),
                "lng": float(lng.strip()),
                "category": c["category"],
                "status": c.get("status", "pending")
            })

    return jsonify({
        "total": total,
        "pending": pending,
        "in_progress": in_progress,
        "resolved": resolved,
        "rejected": rejected,
        "avg_resolution_time": avg_resolution_time,
        "authorities": authorities,
        "locations": locations
    })