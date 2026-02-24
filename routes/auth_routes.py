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
    data = request.get_json()
    required = ['name', 'email', 'phone', 'password', 'role']

    for f in required:
        if f not in data or not data[f]:
            return jsonify({'error': f'{f} is required'}), 400

    # 🔐 Role validation
    if data['role'] not in ['citizen', 'officer']:
        return jsonify({'error': 'Invalid role'}), 400

    db = get_db()

    if db.users.find_one({'email': data['email']}):
        return jsonify({'error': 'Email already registered'}), 400

    user = {
        'name': data['name'],
        'email': data['email'],
        'phone': data['phone'],
        'password': hash_password(data['password']),
        'role': data['role'],
        'created_at': datetime.utcnow()
    }

    result = db.users.insert_one(user)
    user['_id'] = str(result.inserted_id)
    user.pop('password')

    # ✅ Calculate real-time statistics
    user['complaints_submitted'] = 0  # New user, no complaints yet
    user['complaints_resolved'] = 0

    return jsonify({
        'success': True,
        'message': 'Registered successfully',
        'user': user
    }), 201


# ================= LOGIN =================
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    db = get_db()

    user = db.users.find_one({'email': data.get('email')})

    if not user or not verify_password(data.get('password', ''), user['password']):
        return jsonify({'error': 'Invalid credentials'}), 401

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