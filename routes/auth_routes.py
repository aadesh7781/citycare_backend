from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime, timedelta
import jwt
import bcrypt
import os

from utils.database import get_db
from middleware.auth_middleware import token_required

auth_bp = Blueprint('auth', __name__)

JWT_SECRET = os.getenv('JWT_SECRET_KEY', 'citycare-secret')  # ✅ fallback


# ================= TOKEN =================
def generate_token(user):
    payload = {
        'user_id': str(user['_id']),
        'email': user['email'],
        'role': user.get('role', 'citizen'),
        'exp': datetime.utcnow() + timedelta(hours=24)
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')

    # ✅ PyJWT compatibility
    return token if isinstance(token, str) else token.decode('utf-8')


# ================= PASSWORD =================
def hash_password(password: str):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())


def verify_password(password: str, hashed: bytes):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)


# ================= REGISTER =================
@auth_bp.route('/register', methods=['POST'])
def register():
    # Support both JSON and multipart/form-data (for document upload)
    if request.content_type and 'multipart' in request.content_type:
        name     = request.form.get('name')
        email    = request.form.get('email')
        phone    = request.form.get('phone')
        password = request.form.get('password')
    else:
        data     = request.get_json() or {}
        name     = data.get('name')
        email    = data.get('email')
        phone    = data.get('phone')
        password = data.get('password')

    for field, val in [('name', name), ('email', email), ('phone', phone), ('password', password)]:
        if not val:
            return jsonify({'error': f'{field} is required'}), 400

    db = get_db()

    if db.users.find_one({'email': email}):
        return jsonify({'error': 'Email already registered'}), 400

    # ── Document upload (Cloudinary) ──
    doc_url = None
    if 'document' in request.files:
        file = request.files['document']
        if file and file.filename:
            import cloudinary.uploader
            result  = cloudinary.uploader.upload(file, folder='citycare_verification_docs')
            doc_url = result.get('secure_url')

    user = {
        'name'                 : name,
        'email'                : email,
        'phone'                : phone,
        'password'             : hash_password(password),
        'role'                 : 'citizen',
        'verification_status'  : 'pending' if doc_url else 'unsubmitted',
        'verification_document': doc_url,
        'is_banned'            : False,
        'created_at'           : datetime.utcnow(),
    }

    result = db.users.insert_one(user)

    return jsonify({
        'success'             : True,
        'message'             : 'Registered successfully. Waiting for admin verification.',
        'verification_status' : user['verification_status'],
    }), 201


# ================= LOGIN =================
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    db = get_db()

    user = db.users.find_one({'email': data.get('email')})

    if not user or not verify_password(data.get('password', ''), user['password']):
        return jsonify({'error': 'Invalid credentials'}), 401

    # ── Ban check ──
    if user.get('is_banned'):
        return jsonify({'error': 'Your account has been banned. Contact admin.'}), 403

    # ── Verification check (citizens only) ──
    if user.get('role') == 'citizen':
        vstatus = user.get('verification_status', 'pending')
        if vstatus == 'pending':
            return jsonify({'error': 'Your account is pending admin verification. Please wait.', 'verification_status': 'pending'}), 403
        if vstatus == 'rejected':
            note = user.get('verification_note', '')
            return jsonify({'error': f'Your verification was rejected. {note}', 'verification_status': 'rejected'}), 403
        if vstatus == 'unsubmitted':
            return jsonify({'error': 'Please upload your identity document to complete registration.', 'verification_status': 'unsubmitted'}), 403

    token = generate_token(user)

    user['_id'] = str(user['_id'])
    user_id = ObjectId(user['_id'])
    user.pop('password')

    # 🆕 Calculate real-time statistics from complaints collection
    complaints_submitted = db.complaints.count_documents({'user_id': user_id})
    complaints_resolved = db.complaints.count_documents({'user_id': user_id, 'status': 'resolved'})

    user['complaints_submitted'] = complaints_submitted
    user['complaints_resolved'] = complaints_resolved

    return jsonify({
        'success': True,
        'token': token,
        'role': user['role'],   # 🔥 frontend routing ke liye
        'user': user
    }), 200


# ================= CURRENT USER =================
@auth_bp.route('/me', methods=['GET'])
@token_required
def me(current_user):
    db = get_db()
    user = db.users.find_one({'_id': ObjectId(current_user['user_id'])})

    if not user:
        return jsonify({'error': 'User not found'}), 404

    user['_id'] = str(user['_id'])
    user_id = ObjectId(user['_id'])
    user.pop('password')

    # 🆕 Calculate real-time statistics from complaints collection
    # This ensures the profile page always shows current, accurate numbers
    complaints_submitted = db.complaints.count_documents({'user_id': user_id})
    complaints_resolved = db.complaints.count_documents({'user_id': user_id, 'status': 'resolved'})

    user['complaints_submitted'] = complaints_submitted
    user['complaints_resolved'] = complaints_resolved

    return jsonify({'user': user}), 200