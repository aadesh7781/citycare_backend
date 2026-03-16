from flask import Blueprint, jsonify, request
from utils.database import get_db
from datetime import datetime, timezone, timedelta

analytics_bp = Blueprint("analytics", __name__)


def _date_filter(period: str) -> dict:
    """Return MongoDB date filter based on period string."""
    now = datetime.now(timezone.utc)
    if period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start = now - timedelta(days=7)
    elif period == "month":
        start = now - timedelta(days=30)
    else:  # "all"
        return {}
    return {"created_at": {"$gte": start}}


@analytics_bp.route("/home-stats", methods=["GET"])
def home_stats():
    db = get_db()
    now         = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    return jsonify({
        "today_complaints": db.complaints.count_documents({"created_at": {"$gte": today_start}}),
        "today_resolved"  : db.complaints.count_documents({"status": "resolved", "created_at": {"$gte": today_start}}),
        "today_pending"   : db.complaints.count_documents({"status": "pending",  "created_at": {"$gte": today_start}}),
    })


@analytics_bp.route("/summary", methods=["GET"])
def analytics_summary():
    db     = get_db()
    period = request.args.get("period", "all")   # today | week | month | all
    dfilter = _date_filter(period)

    total       = db.complaints.count_documents(dfilter)
    pending     = db.complaints.count_documents({**dfilter, "status": "pending"})
    in_progress = db.complaints.count_documents({**dfilter, "status": "in_progress"})
    resolved    = db.complaints.count_documents({**dfilter, "status": "resolved"})
    rejected    = db.complaints.count_documents({**dfilter, "status": "rejected"})

    # ── Avg resolution time ──
    avg_resolution_time = "N/A"
    query = {**dfilter, "status": "resolved", "resolved_at": {"$exists": True}}
    resolved_complaints = list(db.complaints.find(query))

    if resolved_complaints:
        total_hours = 0
        count       = 0
        for c in resolved_complaints:
            ca = c.get("created_at")
            ra = c.get("resolved_at")
            if ca and ra:
                if isinstance(ca, str):
                    ca = datetime.fromisoformat(ca.replace('Z', '+00:00'))
                if isinstance(ra, str):
                    ra = datetime.fromisoformat(ra.replace('Z', '+00:00'))
                total_hours += (ra - ca).total_seconds() / 3600
                count += 1
        if count > 0:
            avg = total_hours / count
            if avg < 1:
                avg_resolution_time = f"{int(avg * 60)} mins"
            elif avg < 24:
                avg_resolution_time = f"{avg:.1f} hrs"
            else:
                avg_resolution_time = f"{avg/24:.1f} days"

    # ── Category breakdown ──
    match_stage = {"$match": dfilter} if dfilter else {"$match": {}}
    pipeline = [
        match_stage,
        {"$group": {"_id": "$category", "count": {"$sum": 1}}}
    ]
    authorities = [
        {"authority": a["_id"], "count": a["count"]}
        for a in db.complaints.aggregate(pipeline)
    ]

    # ── Locations ──
    loc_query = {**dfilter}
    locations = []
    for c in db.complaints.find(loc_query, {"location": 1, "category": 1, "status": 1}):
        loc = c.get("location", "")
        if "," in loc:
            try:
                lat, lng = loc.split(",")
                locations.append({
                    "lat"     : float(lat.strip()),
                    "lng"     : float(lng.strip()),
                    "category": c.get("category", ""),
                    "status"  : c.get("status", "pending"),
                })
            except:
                pass

    return jsonify({
        "total"              : total,
        "pending"            : pending,
        "in_progress"        : in_progress,
        "resolved"           : resolved,
        "rejected"           : rejected,
        "avg_resolution_time": avg_resolution_time,
        "authorities"        : authorities,
        "locations"          : locations,
        "period"             : period,
    })