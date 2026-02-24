from flask import Blueprint, jsonify
from bson import ObjectId
from utils.database import get_db
from middleware.auth_middleware import token_required

user_bp = Blueprint('users', __name__)

@user_bp.route('/profile', methods=['GET'])
@token_required
def profile(current_user):
    db = get_db()
    user = db.users.find_one({'_id': ObjectId(current_user['user_id'])})
    user['_id'] = str(user['_id'])
    user.pop('password')
    return jsonify({'user': user}), 200
