from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from dotenv import load_dotenv
import os

# ================= CLOUDINARY IMPORT =================
import cloudinary
import cloudinary.uploader
import cloudinary.api

# ================= ENV =================
load_dotenv()

# ================= IMPORT ROUTES =================
from routes.auth_routes import auth_bp
from routes.complaint_routes import complaint_bp
from routes.complaints import complaints_bp
from routes.user_routes import user_bp
from routes.analytics_routes import analytics_bp
from routes.officer_routes import officer_bp
from routes.authorities_routes import authorities_bp
from routes.chatbot_routes import chatbot_bp
from routes.fcm_routes import fcm_bp

# ================= DATABASE =================
from utils.database import init_db

# ================= APP INIT =================
app = Flask(__name__)

# ================= CLOUDINARY CONFIG =================
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
    secure=True
)

# ================= CONFIG =================
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "your-secret-key")
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "your-jwt-secret")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

# ================= CORS =================
CORS(
    app,
    resources={
        r"/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Type", "Authorization"],
        }
    },
    supports_credentials=False,
    send_wildcard=True,
    always_send=True,
)

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify({"status": "ok"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
        response.headers.add("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
        response.headers.add("Access-Control-Max-Age", "3600")
        return response, 200

@app.before_request
def log_request():
    print(f"\n{'='*70}")
    print(f"📥 {request.method} {request.path}")
    print(f"   Origin: {request.headers.get('Origin', 'None')}")
    if request.headers.get('Authorization'):
        print(f"   Auth: {request.headers.get('Authorization')[:30]}...")
    print(f"{'='*70}")

@app.after_request
def add_cors_headers(response):
    if not response.headers.get('Access-Control-Allow-Origin'):
        response.headers['Access-Control-Allow-Origin'] = '*'
    if not response.headers.get('Access-Control-Allow-Methods'):
        response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
    if not response.headers.get('Access-Control-Allow-Headers'):
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'

    print(f"📤 Response: {response.status}")
    print(f"   CORS: {response.headers.get('Access-Control-Allow-Origin')}")
    return response

# ================= DB INIT =================
init_db()

# ================= REGISTER BLUEPRINTS =================
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(complaint_bp, url_prefix="/api/complaints")
app.register_blueprint(user_bp, url_prefix="/api/users")
app.register_blueprint(complaints_bp, url_prefix="/api/public")
app.register_blueprint(analytics_bp, url_prefix="/api/analytics")
app.register_blueprint(officer_bp, url_prefix="/api/officer")
app.register_blueprint(authorities_bp, url_prefix="/api/authorities")
app.register_blueprint(chatbot_bp, url_prefix="/api/chatbot")
app.register_blueprint(fcm_bp, url_prefix="/api/fcm")

# ================= IMAGE SERVING (OLD - KEEPING FOR SAFETY) =================
@app.route("/uploads/<path:filename>")
def serve_uploaded_files(filename):
    upload_root = os.path.join(os.getcwd(), "uploads")
    return send_from_directory(upload_root, filename)

# ================= ROOT =================
@app.route("/")
def index():
    return jsonify({
        "message": "CityCare API is running",
        "version": "1.0.0",
        "modules": {
            "auth": "/api/auth",
            "user_complaints": "/api/complaints",
            "public_complaints": "/api/public/complaints/all",
            "analytics": "/api/analytics/summary",
            "officer": "/api/officer/complaints",
            "authorities": "/api/authorities",
            "chatbot": "/api/chatbot/message",
            "fcm": "/api/fcm/register-token",
            "uploads": "Now using Cloudinary"
        }
    })

# ================= HEALTH =================
@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

# ================= ERRORS =================
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(413)
def file_too_large(error):
    return jsonify({"error": "File too large. Max 16MB"}), 413

# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.getenv("FLASK_DEBUG", "False") == "True"

    print("\n" + "="*70)
    print("🚀 CITYCARE BACKEND - WITH CLOUDINARY + FIREBASE")
    print("="*70)
    print(f"✅ CORS: Enabled")
    print(f"✅ Cloudinary: Enabled")
    print(f"✅ Firebase: Enabled")
    print(f"✅ Running on Port: {port}")
    print("="*70 + "\n")

    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug_mode,
    )