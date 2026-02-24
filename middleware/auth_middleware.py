import jwt
from flask import request, jsonify
import os

def token_required(f):
    def wrapper(*args, **kwargs):
        token = None

        if "Authorization" in request.headers:
            token = request.headers["Authorization"].split(" ")[1]

        if not token:
            return jsonify({"error": "Token missing"}), 401

        try:
            data = jwt.decode(
                token,
                os.getenv("JWT_SECRET_KEY"),
                algorithms=["HS256"]
            )
            current_user = {
                "user_id": data["user_id"],
                "role": data.get("role", "citizen")
            }
        except Exception:
            return jsonify({"error": "Invalid token"}), 401

        return f(current_user, *args, **kwargs)

    wrapper.__name__ = f.__name__
    return wrapper
