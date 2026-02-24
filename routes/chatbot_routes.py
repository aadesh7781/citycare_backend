from flask import Blueprint, request, jsonify
from datetime import datetime
import re

chatbot_bp = Blueprint('chatbot', __name__)

# ================= CHATBOT KNOWLEDGE BASE =================

class NagrikBot:
    """
    NagrikBot - Your friendly CityCare assistant
    Name meaning: 'Nagrik' = Citizen in Hindi
    """

    def __init__(self):
        self.name = "NagrikBot"
        self.greeting_keywords = ['hello', 'hi', 'hey', 'namaste', 'namaskar']
        self.name_keywords = ['name', 'who are you', 'naam', 'aap kaun']

        # Knowledge base for CityCare services
        self.knowledge_base = {
            'complaint_categories': {
                'roads': {
                    'name': 'Roads',
                    'description': 'Report potholes, road damage, broken pavements, traffic issues',
                    'examples': ['pothole', 'road damage', 'pavement', 'street light', 'traffic'],
                    'hindi': 'सड़क - गड्ढे, सड़क क्षति, फुटपाथ की समस्याएं'
                },
                'sanitation': {
                    'name': 'Sanitation',
                    'description': 'Report garbage collection, waste disposal, cleanliness issues',
                    'examples': ['garbage', 'waste', 'dustbin', 'cleanliness', 'littering'],
                    'hindi': 'स्वच्छता - कचरा संग्रहण, सफाई समस्याएं'
                },
                'water': {
                    'name': 'Water Supply',
                    'description': 'Report water shortage, leakage, contamination, supply issues',
                    'examples': ['water', 'leakage', 'shortage', 'contamination', 'supply'],
                    'hindi': 'जल आपूर्ति - पानी की कमी, रिसाव'
                },
                'electricity': {
                    'name': 'Electricity',
                    'description': 'Report power cuts, wire issues, transformer problems',
                    'examples': ['electricity', 'power cut', 'transformer', 'wire', 'outage'],
                    'hindi': 'बिजली - बिजली कटौती, तार की समस्या'
                },
                'drainage': {
                    'name': 'Drainage',
                    'description': 'Report blocked drains, sewage overflow, manhole issues',
                    'examples': ['drainage', 'sewage', 'manhole', 'blocked drain', 'overflow'],
                    'hindi': 'नाली - अवरुद्ध नालियां, सीवेज समस्याएं'
                }
            },

            'status_meanings': {
                'pending': 'Your complaint has been registered and is waiting for review',
                'in_progress': 'An officer has been assigned and is working on your complaint',
                'resolved': 'Your complaint has been resolved. Please provide feedback',
                'rejected': 'Your complaint was reviewed and could not be processed'
            },

            'features': {
                'submit_complaint': {
                    'title': 'Submit Complaint',
                    'description': 'Register a new civic issue with photo and location',
                    'steps': [
                        '1. Click on "Raise Complaint" on home screen',
                        '2. Select category (Roads, Sanitation, Water, Electricity, Drainage)',
                        '3. Take or upload a photo of the issue',
                        '4. Add location (automatic or manual)',
                        '5. Write description',
                        '6. Submit'
                    ]
                },
                'track_complaints': {
                    'title': 'Track My Complaints',
                    'description': 'View all your submitted complaints and their status',
                    'info': 'Access from Home → My Complaints or Complaints tab'
                },
                'view_all_complaints': {
                    'title': 'All Complaints',
                    'description': 'See all public complaints in your city',
                    'info': 'Helps you see if someone already reported a similar issue'
                },
                'analytics': {
                    'title': 'Analytics',
                    'description': 'View city-wide statistics and complaint trends',
                    'metrics': ['Total complaints', 'By category', 'Resolution rate', 'Response time']
                },
                'authorities': {
                    'title': 'Authorities',
                    'description': 'View all municipal officers and departments',
                    'info': 'See who is responsible for different areas'
                },
                'profile': {
                    'title': 'Profile',
                    'description': 'Manage your account, view stats, and settings'
                },
                'feedback': {
                    'title': 'Feedback System',
                    'description': 'Rate and review resolved complaints',
                    'info': 'Help improve city services with your feedback'
                }
            },

            'faqs': [
                {
                    'q': 'How long does it take to resolve a complaint?',
                    'a': 'Resolution time varies by category: Roads (3-7 days), Sanitation (1-3 days), Water Supply (1-2 days), Electricity (Same day), Drainage (2-5 days)'
                },
                {
                    'q': 'Can I track my complaint status?',
                    'a': 'Yes! Go to "My Complaints" section to see real-time status updates of all your complaints'
                },
                {
                    'q': 'Do I need to upload a photo?',
                    'a': 'While not mandatory, photos help officers understand and resolve issues faster'
                },
                {
                    'q': 'Can I edit my complaint after submission?',
                    'a': 'No, but you can view complaint details and contact the assigned officer if needed'
                },
                {
                    'q': 'What if my complaint is rejected?',
                    'a': 'Check the rejection reason in complaint details. You can submit a new complaint with more information'
                },
                {
                    'q': 'Can I see complaints from other users?',
                    'a': 'Yes, go to "All Complaints" tab to see all public complaints in your city'
                },
                {
                    'q': 'How do I provide feedback?',
                    'a': 'Once your complaint is resolved, you will see a feedback button. Rate and review the service'
                },
                {
                    'q': 'Is my data safe?',
                    'a': 'Yes, we use secure authentication and your personal data is protected'
                }
            ],

            'tips': [
                '📸 Always include a clear photo of the issue for faster resolution',
                '📍 Accurate location helps officers reach the spot quickly',
                '📝 Provide detailed description - mention landmarks if possible',
                '⏰ Check complaint status regularly for updates',
                '⭐ Give feedback after resolution to improve city services',
                '🔔 Enable notifications to get real-time updates',
                '👥 Check "All Complaints" to avoid duplicate reports'
            ]
        }

    def get_response(self, user_message):
        """Generate intelligent response based on user query"""
        message_lower = user_message.lower().strip()

        # Greetings
        if any(keyword in message_lower for keyword in self.greeting_keywords):
            return self._greeting_response()

        # Name inquiry
        if any(keyword in message_lower for keyword in self.name_keywords):
            return self._name_response()

        # Help/Menu
        if any(word in message_lower for word in ['help', 'menu', 'features', 'what can', 'madad']):
            return self._help_response()

        # Complaint submission
        if any(word in message_lower for word in ['submit', 'register', 'file', 'complaint', 'report', 'shikayat']):
            return self._complaint_submission_guide()

        # Complaint categories
        if any(word in message_lower for word in ['category', 'categories', 'types', 'shrenikaran']):
            return self._categories_response()

        # Specific category queries
        for category, data in self.knowledge_base['complaint_categories'].items():
            if any(example in message_lower for example in data['examples']):
                return self._category_specific_response(data)

        # Status tracking
        if any(word in message_lower for word in ['status', 'track', 'check', 'where', 'sthiti']):
            return self._status_tracking_guide()

        # Timeline/duration
        if any(word in message_lower for word in ['how long', 'duration', 'time', 'kitna samay']):
            return self._resolution_timeline()

        # Features
        if any(word in message_lower for word in ['analytics', 'statistics', 'data', 'ankde']):
            return self._analytics_info()

        if any(word in message_lower for word in ['authorities', 'officers', 'adhikari']):
            return self._authorities_info()

        if any(word in message_lower for word in ['feedback', 'rating', 'review', 'pratikruya']):
            return self._feedback_info()

        # FAQs
        if 'photo' in message_lower or 'image' in message_lower or 'picture' in message_lower:
            return self._photo_faq()

        if 'edit' in message_lower or 'change' in message_lower or 'modify' in message_lower:
            return self._edit_faq()

        if 'reject' in message_lower or 'rejected' in message_lower:
            return self._rejection_faq()

        # Tips
        if any(word in message_lower for word in ['tip', 'tips', 'advice', 'suggestion', 'sujhav']):
            return self._tips_response()

        # Default - show FAQs
        return self._default_response(message_lower)

    def _greeting_response(self):
        return {
            'message': f"Namaste! 🙏 I'm {self.name}, your CityCare assistant. I'm here to help you with civic complaints and city services.\n\nI can help you with:\n• 📝 Submit complaints\n• 📊 Track complaint status\n• ℹ️ Learn about features\n• ❓ Answer your questions\n\nHow can I assist you today?",
            'quick_actions': [
                'Submit complaint',
                'Track status',
                'View categories',
                'Show menu'
            ]
        }

    def _name_response(self):
        return {
            'message': f"I'm {self.name}! 😊\n\n'Nagrik' means 'Citizen' in Hindi - because I'm here to serve you, the citizen!\n\nI'm your friendly assistant for all CityCare services. Think of me as your guide to making your city better. How can I help you today?",
            'quick_actions': ['What can you do?', 'Submit complaint', 'Help']
        }

    def _help_response(self):
        features_text = "📱 CityCare Features:\n\n"
        for key, feature in self.knowledge_base['features'].items():
            features_text += f"• {feature['title']}\n  {feature['description']}\n\n"

        features_text += "Ask me anything about these features!"

        return {
            'message': features_text,
            'quick_actions': [
                'Submit complaint',
                'View categories',
                'Check status',
                'Show tips'
            ]
        }

    def _complaint_submission_guide(self):
        steps = self.knowledge_base['features']['submit_complaint']['steps']
        steps_text = "📝 How to Submit a Complaint:\n\n" + "\n".join(steps)
        steps_text += "\n\n💡 Tip: Include a photo and accurate location for faster resolution!"

        return {
            'message': steps_text,
            'quick_actions': [
                'View categories',
                'What categories?',
                'Resolution time',
                'Tips'
            ]
        }

    def _categories_response(self):
        categories_text = "📋 Complaint Categories:\n\n"
        for category, data in self.knowledge_base['complaint_categories'].items():
            categories_text += f"🔹 {data['name']}\n"
            categories_text += f"   {data['description']}\n\n"

        categories_text += "Which category would you like to know more about?"

        return {
            'message': categories_text,
            'quick_actions': ['Roads', 'Sanitation', 'Water Supply', 'Electricity']
        }

    def _category_specific_response(self, category_data):
        response = f"ℹ️ {category_data['name']} Complaints\n\n"
        response += f"{category_data['description']}\n\n"
        response += f"📝 Examples: {', '.join(category_data['examples'][:3])}\n"
        response += f"🇮🇳 हिंदी: {category_data['hindi']}\n\n"
        response += "Ready to submit a complaint in this category?"

        return {
            'message': response,
            'quick_actions': ['Submit complaint', 'Other categories', 'Resolution time']
        }

    def _status_tracking_guide(self):
        status_info = "📊 Track Your Complaint:\n\n"
        status_info += "Go to Home → 'My Complaints' to see all your submissions\n\n"
        status_info += "Status Meanings:\n"

        for status, meaning in self.knowledge_base['status_meanings'].items():
            icon = {'pending': '⏳', 'in_progress': '🔄', 'resolved': '✅', 'rejected': '❌'}
            status_info += f"{icon.get(status, '•')} {status.title()}: {meaning}\n\n"

        return {
            'message': status_info,
            'quick_actions': ['Submit complaint', 'Resolution time', 'Feedback']
        }

    def _resolution_timeline(self):
        timeline = "⏰ Expected Resolution Time:\n\n"
        timeline += "🔧 Electricity: Same day\n"
        timeline += "💧 Water Supply: 1-2 days\n"
        timeline += "🗑️ Sanitation: 1-3 days\n"
        timeline += "🚰 Drainage: 2-5 days\n"
        timeline += "🛣️ Roads: 3-7 days\n\n"
        timeline += "Note: Actual time may vary based on issue severity and resource availability"

        return {
            'message': timeline,
            'quick_actions': ['Submit complaint', 'Track status', 'Tips']
        }

    def _analytics_info(self):
        info = self.knowledge_base['features']['analytics']
        response = f"📊 {info['title']}\n\n{info['description']}\n\n"
        response += "View insights like:\n"
        for metric in info['metrics']:
            response += f"• {metric}\n"
        response += "\nAccess from the Analytics tab at the bottom!"

        return {
            'message': response,
            'quick_actions': ['Authorities', 'Submit complaint', 'Menu']
        }

    def _authorities_info(self):
        info = self.knowledge_base['features']['authorities']
        response = f"👮 {info['title']}\n\n{info['description']}\n\n{info['info']}\n\n"
        response += "You can view officer details, contact information, and assigned areas.\n\n"
        response += "Access from the Authorities tab!"

        return {
            'message': response,
            'quick_actions': ['Analytics', 'Submit complaint', 'Menu']
        }

    def _feedback_info(self):
        info = self.knowledge_base['features']['feedback']
        response = f"⭐ {info['title']}\n\n{info['description']}\n\n{info['info']}\n\n"
        response += "After your complaint is resolved:\n"
        response += "1. Go to 'My Complaints'\n"
        response += "2. Click on the resolved complaint\n"
        response += "3. Tap 'Submit Feedback'\n"
        response += "4. Rate (1-5 stars) and add comments\n\n"
        response += "Your feedback helps improve city services! 🙏"

        return {
            'message': response,
            'quick_actions': ['Track status', 'Submit complaint', 'Tips']
        }

    def _photo_faq(self):
        faq = next(f for f in self.knowledge_base['faqs'] if 'photo' in f['q'].lower())
        return {
            'message': f"❓ {faq['q']}\n\n💡 {faq['a']}\n\nPhotos significantly improve resolution time by helping officers:\n• Understand the issue better\n• Assess severity\n• Plan resources\n• Verify after resolution",
            'quick_actions': ['Submit complaint', 'Other FAQs', 'Tips']
        }

    def _edit_faq(self):
        faq = next(f for f in self.knowledge_base['faqs'] if 'edit' in f['q'].lower())
        return {
            'message': f"❓ {faq['q']}\n\n💡 {faq['a']}\n\nIf you need to add more information:\n• Wait for officer to contact you, or\n• Submit a new complaint with updated details\n• Reference the old complaint ID in description",
            'quick_actions': ['Track status', 'Submit complaint', 'Contact']
        }

    def _rejection_faq(self):
        faq = next(f for f in self.knowledge_base['faqs'] if 'reject' in f['q'].lower())
        return {
            'message': f"❓ {faq['q']}\n\n💡 {faq['a']}\n\nCommon rejection reasons:\n• Duplicate complaint\n• Insufficient information\n• Not under municipal jurisdiction\n• Issue already resolved\n\nReview and submit with more details if needed!",
            'quick_actions': ['Submit complaint', 'Categories', 'Tips']
        }

    def _tips_response(self):
        tips_text = "💡 Pro Tips for Better Results:\n\n"
        for i, tip in enumerate(self.knowledge_base['tips'], 1):
            tips_text += f"{tip}\n"
            if i < len(self.knowledge_base['tips']):
                tips_text += "\n"

        return {
            'message': tips_text,
            'quick_actions': ['Submit complaint', 'Track status', 'FAQs']
        }

    def _default_response(self, user_message):
        # Try to match with FAQs
        for faq in self.knowledge_base['faqs']:
            if any(word in user_message for word in faq['q'].lower().split()):
                return {
                    'message': f"❓ {faq['q']}\n\n💡 {faq['a']}",
                    'quick_actions': ['Submit complaint', 'More FAQs', 'Help']
                }

        # Generic helpful response
        return {
            'message': f"I'm here to help! 😊\n\nI can assist you with:\n\n• 📝 Submitting complaints\n• 📊 Tracking complaint status\n• ℹ️ Understanding features\n• ❓ Answering questions about CityCare\n\nWhat would you like to know?",
            'quick_actions': [
                'Submit complaint',
                'View categories',
                'Track status',
                'Show menu'
            ]
        }

# ================= ROUTES =================

nagrik_bot = NagrikBot()

@chatbot_bp.route('/message', methods=['POST'])
def chat_message():
    """
    Handle chat messages
    """
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()

        if not user_message:
            return jsonify({
                'success': False,
                'error': 'Message is required'
            }), 400

        # Get bot response
        response = nagrik_bot.get_response(user_message)

        return jsonify({
            'success': True,
            'bot_name': nagrik_bot.name,
            'response': response['message'],
            'quick_actions': response.get('quick_actions', []),
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        print(f"❌ Chatbot error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to process message',
            'bot_name': nagrik_bot.name,
            'response': "I apologize, I'm having trouble understanding. Please try asking in a different way or type 'help' to see what I can do! 😊"
        }), 500

@chatbot_bp.route('/quick-action', methods=['POST'])
def quick_action():
    """
    Handle quick action button clicks
    """
    try:
        data = request.get_json()
        action = data.get('action', '').strip()

        if not action:
            return jsonify({
                'success': False,
                'error': 'Action is required'
            }), 400

        # Treat quick action as a message
        response = nagrik_bot.get_response(action)

        return jsonify({
            'success': True,
            'bot_name': nagrik_bot.name,
            'response': response['message'],
            'quick_actions': response.get('quick_actions', []),
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        print(f"❌ Quick action error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to process action'
        }), 500

@chatbot_bp.route('/info', methods=['GET'])
def bot_info():
    """
    Get chatbot information
    """
    return jsonify({
        'success': True,
        'bot_name': nagrik_bot.name,
        'description': 'Your friendly CityCare assistant - Nagrik means Citizen in Hindi',
        'capabilities': [
            'Answer questions about CityCare',
            'Guide through complaint submission',
            'Explain features and statuses',
            'Provide tips and FAQs',
            'Support in English and Hindi'
        ],
        'version': '1.0.0'
    })