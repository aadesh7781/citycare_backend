"""
Firebase Cloud Messaging Service
Handles sending push notifications to Flutter app
"""
import os
import json
import tempfile
import requests
from typing import List, Dict, Optional
from datetime import datetime


def _write_firebase_credentials() -> Optional[str]:
    """Write Firebase credentials from env var to a temp file, return path."""
    firebase_json = os.environ.get("FIREBASE_JSON")
    if firebase_json:
        try:
            tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            tmp.write(firebase_json)
            tmp.close()
            print("✅ Firebase credentials loaded from FIREBASE_JSON env var")
            return tmp.name
        except Exception as e:
            print(f"❌ Error writing Firebase credentials from env var: {e}")

    # Fallback to local file
    fallback = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-service-account.json")
    if os.path.exists(fallback):
        print(f"✅ Firebase credentials loaded from file: {fallback}")
        return fallback

    print("❌ No Firebase credentials found (FIREBASE_JSON env var or file)")
    return None


class FirebaseService:
    def __init__(self):
        self.credentials_path = _write_firebase_credentials()
        self.fcm_url = "https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"

    def _get_access_token(self) -> Optional[str]:
        if not self.credentials_path:
            print("❌ No Firebase credentials available")
            return None
        try:
            from google.auth.transport.requests import Request
            from google.oauth2 import service_account

            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=["https://www.googleapis.com/auth/firebase.messaging"]
            )
            credentials.refresh(Request())
            return credentials.token

        except FileNotFoundError:
            print(f"❌ Firebase credentials file not found: {self.credentials_path}")
            return None
        except Exception as e:
            print(f"❌ Error getting Firebase access token: {e}")
            return None

    def _get_project_id(self) -> Optional[str]:
        if not self.credentials_path:
            return None
        try:
            with open(self.credentials_path, 'r') as f:
                return json.load(f).get('project_id')
        except Exception as e:
            print(f"❌ Error reading project ID: {e}")
            return None

    def send_notification(
            self,
            token: str,
            title: str,
            body: str,
            data: Optional[Dict] = None
    ) -> bool:
        """
        Send FCM notification with BOTH notification and data payloads.
        - notification payload: Makes it appear in system tray automatically
        - data payload: Allows in-app handling and custom actions
        """
        if not token:
            print("⚠️ No FCM token provided")
            return False

        access_token = self._get_access_token()
        if not access_token:
            print("⚠️ Could not get Firebase access token")
            return False

        project_id = self._get_project_id()
        if not project_id:
            print("⚠️ Could not get Firebase project ID")
            return False

        try:
            url = self.fcm_url.format(project_id=project_id)

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            # Prepare data payload (all values must be strings)
            payload_data = {
                "title": str(title),
                "body": str(body),
                "click_action": "FLUTTER_NOTIFICATION_CLICK",
            }
            if data:
                payload_data.update({k: str(v) for k, v in data.items()})

            message = {
                "message": {
                    "token": token,

                    # ✅ NOTIFICATION PAYLOAD - Makes it appear in system tray
                    "notification": {
                        "title": title,
                        "body": body,
                    },

                    # ✅ DATA PAYLOAD - For in-app handling
                    "data": payload_data,

                    # Android-specific config
                    "android": {
                        "priority": "high",
                        "notification": {
                            "channel_id": "citycare_channel",
                            "sound": "default",
                            "default_vibrate_timings": True,
                            "notification_priority": "PRIORITY_HIGH",
                        }
                    },

                    # iOS-specific config
                    "apns": {
                        "headers": {
                            "apns-priority": "10",
                        },
                        "payload": {
                            "aps": {
                                "alert": {
                                    "title": title,
                                    "body": body,
                                },
                                "sound": "default",
                                "badge": 1,
                            }
                        }
                    }
                }
            }

            print(f"📤 Sending FCM notification:")
            print(f"   Token: {token[:30]}...")
            print(f"   Title: {title}")
            print(f"   Body: {body}")

            response = requests.post(url, headers=headers, json=message)

            if response.status_code == 200:
                print(f"✅ Notification sent successfully!")
                return True
            else:
                print(f"❌ Failed to send notification: {response.status_code}")
                print(f"   Response: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Error sending notification: {e}")
            import traceback
            traceback.print_exc()
            return False

    def send_to_multiple(
            self,
            tokens: List[str],
            title: str,
            body: str,
            data: Optional[Dict] = None
    ) -> int:
        """Send notification to multiple tokens"""
        success_count = 0
        for token in tokens:
            if self.send_notification(token, title, body, data):
                success_count += 1
        print(f"📊 Sent to {success_count}/{len(tokens)} devices")
        return success_count

    # ================= HELPER METHODS =================

    def notify_new_complaint(
            self,
            officer_tokens: List[str],
            complaint_id: str,
            category: str,
            location: str,
            urgency: int
    ) -> int:
        """Notify officers of new complaint"""
        title = "🚨 New Complaint Received"
        body = f"{category} complaint in {location} (Urgency: {urgency})"
        data = {
            "type": "new_complaint",
            "complaint_id": complaint_id,
            "category": category,
            "urgency": str(urgency),
            "timestamp": datetime.utcnow().isoformat()
        }
        return self.send_to_multiple(officer_tokens, title, body, data)

    def notify_status_update(
            self,
            user_token: str,
            complaint_id: str,
            new_status: str,
            category: str
    ) -> bool:
        """Notify citizen of complaint status update"""
        status_messages = {
            "in_progress": "🔨 Your complaint is now being worked on!",
            "resolved": "✅ Your complaint has been resolved! Please provide feedback.",
            "rejected": "❌ Your complaint was rejected"
        }

        title = "📋 Complaint Status Update"
        body = status_messages.get(new_status, f"Your {category} complaint status updated to {new_status}")

        data = {
            "type": "status_update",
            "complaint_id": complaint_id,
            "status": new_status,
            "category": category,
            "timestamp": datetime.utcnow().isoformat()
        }

        print(f"🔔 Sending status update notification:")
        print(f"   Status: {new_status}")
        print(f"   Category: {category}")
        print(f"   Complaint: {complaint_id}")

        return self.send_notification(user_token, title, body, data)

    def notify_feedback_received(
            self,
            officer_token: str,
            complaint_id: str,
            rating: int,
            category: str
    ) -> bool:
        """Notify officer of feedback received"""
        stars = "⭐" * rating
        title = f"📊 Feedback Received {stars}"
        body = f"You received a {rating}-star rating for {category} complaint"
        data = {
            "type": "feedback_received",
            "complaint_id": complaint_id,
            "rating": str(rating),
            "timestamp": datetime.utcnow().isoformat()
        }
        return self.send_notification(officer_token, title, body, data)


# Singleton instance
firebase_service = FirebaseService()