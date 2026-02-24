from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime
import os
from werkzeug.utils import secure_filename

# Assuming you have a MongoDB connection and config
# from app import mongo, UPLOAD_FOLDER
# from middleware.auth import token_required

feedback_bp = Blueprint('feedback', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Submit feedback for resolved complaint
@feedback_bp.route('/api/complaints/<complaint_id>/feedback', methods=['POST'])
# @token_required  # Uncomment when auth is set up
def submit_feedback(complaint_id):
    """
    Submit user feedback for a resolved complaint
    Expected JSON body:
    {
        "rating": 1-5,
        "comment": "optional feedback comment"
    }
    """
    try:
        # Get request data
        data = request.get_json()
        rating = data.get('rating')
        comment = data.get('comment', '')

        # Validate rating
        if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
            return jsonify({
                'error': 'Invalid rating. Must be between 1 and 5'
            }), 400

        # Find complaint
        from app import mongo  # Import your mongo instance
        complaint = mongo.db.complaints.find_one({'_id': ObjectId(complaint_id)})

        if not complaint:
            return jsonify({'error': 'Complaint not found'}), 404

        # Check if complaint is resolved
        if complaint.get('status', '').lower() != 'resolved':
            return jsonify({
                'error': 'Feedback can only be submitted for resolved complaints'
            }), 400

        # Check if feedback already exists
        if complaint.get('feedbackRating'):
            return jsonify({
                'error': 'Feedback already submitted for this complaint'
            }), 400

        # Update complaint with feedback
        mongo.db.complaints.update_one(
            {'_id': ObjectId(complaint_id)},
            {
                '$set': {
                    'feedbackRating': rating,
                    'feedbackComment': comment,
                    'feedbackSubmittedAt': datetime.utcnow()
                }
            }
        )

        # Optionally update officer statistics
        if complaint.get('assignedOfficerId'):
            _update_officer_rating(complaint.get('assignedOfficerId'), rating)

        return jsonify({
            'message': 'Feedback submitted successfully',
            'rating': rating,
            'comment': comment
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Upload proof image for resolved complaint (by officer)
@feedback_bp.route('/api/complaints/<complaint_id>/proof-image', methods=['POST'])
# @token_required  # Uncomment when auth is set up
def upload_proof_image(complaint_id):
    """
    Upload proof/after image for resolved complaint (typically by officer)
    """
    try:
        # Check if image file is present
        if 'proof_image' not in request.files:
            return jsonify({'error': 'No proof image file provided'}), 400

        file = request.files['proof_image']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({
                'error': 'Invalid file type. Only PNG, JPG, JPEG, GIF allowed'
            }), 400

        # Find complaint
        from app import mongo
        complaint = mongo.db.complaints.find_one({'_id': ObjectId(complaint_id)})

        if not complaint:
            return jsonify({'error': 'Complaint not found'}), 404

        # Save the file
        filename = secure_filename(file.filename)
        unique_filename = f"proof_{complaint_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"

        from app import UPLOAD_FOLDER  # Import your upload folder config
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(filepath)

        # Update complaint with proof image URL
        mongo.db.complaints.update_one(
            {'_id': ObjectId(complaint_id)},
            {
                '$set': {
                    'proofImageUrl': unique_filename,
                    'proofImageUploadedAt': datetime.utcnow()
                }
            }
        )

        return jsonify({
            'message': 'Proof image uploaded successfully',
            'proofImageUrl': unique_filename
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Get feedback statistics
@feedback_bp.route('/api/feedback/statistics', methods=['GET'])
# @token_required
def get_feedback_statistics():
    """
    Get overall feedback statistics
    """
    try:
        from app import mongo

        # Get all complaints with feedback
        pipeline = [
            {
                '$match': {
                    'feedbackRating': {'$exists': True, '$ne': None}
                }
            },
            {
                '$group': {
                    '_id': None,
                    'totalFeedbacks': {'$sum': 1},
                    'averageRating': {'$avg': '$feedbackRating'},
                    'ratingDistribution': {
                        '$push': '$feedbackRating'
                    }
                }
            }
        ]

        result = list(mongo.db.complaints.aggregate(pipeline))

        if not result:
            return jsonify({
                'totalFeedbacks': 0,
                'averageRating': 0,
                'ratingDistribution': {
                    '5': 0, '4': 0, '3': 0, '2': 0, '1': 0
                }
            }), 200

        stats = result[0]
        ratings = stats['ratingDistribution']

        # Calculate distribution
        distribution = {
            '5': ratings.count(5),
            '4': ratings.count(4),
            '3': ratings.count(3),
            '2': ratings.count(2),
            '1': ratings.count(1)
        }

        return jsonify({
            'totalFeedbacks': stats['totalFeedbacks'],
            'averageRating': round(stats['averageRating'], 2),
            'ratingDistribution': distribution
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Get feedback for specific complaint
@feedback_bp.route('/api/complaints/<complaint_id>/feedback', methods=['GET'])
# @token_required
def get_complaint_feedback(complaint_id):
    """
    Get feedback for a specific complaint
    """
    try:
        from app import mongo

        complaint = mongo.db.complaints.find_one(
            {'_id': ObjectId(complaint_id)},
            {
                'feedbackRating': 1,
                'feedbackComment': 1,
                'feedbackSubmittedAt': 1
            }
        )

        if not complaint:
            return jsonify({'error': 'Complaint not found'}), 404

        if not complaint.get('feedbackRating'):
            return jsonify({
                'hasFeedback': False,
                'message': 'No feedback submitted yet'
            }), 200

        return jsonify({
            'hasFeedback': True,
            'rating': complaint.get('feedbackRating'),
            'comment': complaint.get('feedbackComment', ''),
            'submittedAt': complaint.get('feedbackSubmittedAt')
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def _update_officer_rating(officer_id, new_rating):
    """
    Helper function to update officer's average rating
    """
    try:
        from app import mongo

        # Calculate new average rating
        officer = mongo.db.officers.find_one({'_id': ObjectId(officer_id)})

        if officer:
            current_rating = officer.get('averageRating', 0)
            total_ratings = officer.get('totalRatings', 0)

            new_average = ((current_rating * total_ratings) + new_rating) / (total_ratings + 1)

            mongo.db.officers.update_one(
                {'_id': ObjectId(officer_id)},
                {
                    '$set': {
                        'averageRating': round(new_average, 2),
                        'totalRatings': total_ratings + 1
                    }
                }
            )
    except Exception as e:
        print(f"Error updating officer rating: {e}")


# Register blueprint in your main app.py:
# from routes.feedback import feedback_bp
# app.register_blueprint(feedback_bp)