from flask import Blueprint, request, jsonify
from bson import ObjectId
from utils.database import get_db
from middleware.auth_middleware import token_required

fcm_bp = Blueprint("fcm", __name__)

@fcm_bp.route("/register-token", methods=["POST"])
@token_required
def register_fcm_token(current_user):
    """
    Register or update FCM device token for push notifications

    Expected body:
    {
        "fcm_token": "device_fcm_token_here"
    }
    """
    db = get_db()

    try:
        data = request.get_json()
        fcm_token = data.get("fcm_token")

        if not fcm_token:
            return jsonify({"error": "FCM token is required"}), 400

        # Update user's FCM token
        result = db.users.update_one(
            {"_id": ObjectId(current_user["user_id"])},
            {
                "$set": {
                    "fcm_token": fcm_token,
                    "fcm_token_updated_at": current_user.get("timestamp")
                }
            }
        )

        if result.matched_count == 0:
            return jsonify({"error": "User not found"}), 404

        print(f"✅ FCM token registered for user {current_user['user_id']}")

        return jsonify({
            "message": "FCM token registered successfully",
            "token_registered": True
        }), 200

    except Exception as e:
        print(f"❌ Error registering FCM token: {e}")
        return jsonify({"error": str(e)}), 500


@fcm_bp.route("/unregister-token", methods=["POST"])
@token_required
def unregister_fcm_token(current_user):
    """
    Unregister FCM token (when user logs out)
    """
    db = get_db()

    try:
        result = db.users.update_one(
            {"_id": ObjectId(current_user["user_id"])},
            {
                "$unset": {
                    "fcm_token": "",
                    "fcm_token_updated_at": ""
                }
            }
        )

        if result.matched_count == 0:
            return jsonify({"error": "User not found"}), 404

        print(f"✅ FCM token unregistered for user {current_user['user_id']}")

        return jsonify({
            "message": "FCM token unregistered successfully"
        }), 200

    except Exception as e:
        print(f"❌ Error unregistering FCM token: {e}")
        return jsonify({"error": str(e)}), 500