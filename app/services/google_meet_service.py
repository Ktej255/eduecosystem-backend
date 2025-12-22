"""
Google Meet Service for Webinar Integration

This service creates Google Meet links for webinars.
For simplicity, we use a link-based approach where:
1. Meeting links can be manually provided by the teacher
2. Or auto-generated using Google Calendar API (requires OAuth setup)

For the auto-generation feature, you need to:
1. Set up Google Cloud Console project
2. Enable Google Calendar API
3. Create OAuth 2.0 credentials
4. Set GOOGLE_CREDENTIALS_PATH in .env
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class GoogleMeetService:
    """Service for creating and managing Google Meet links"""
    
    def __init__(self):
        self.credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH")
        self.calendar_service = None
        self._initialized = False
        
    def _initialize(self):
        """Initialize Google Calendar API client"""
        if self._initialized:
            return
            
        if not self.credentials_path or not os.path.exists(self.credentials_path):
            logger.warning("Google credentials not configured. Using manual link mode.")
            self._initialized = True
            return
            
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            
            SCOPES = ['https://www.googleapis.com/auth/calendar']
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path, scopes=SCOPES
            )
            self.calendar_service = build('calendar', 'v3', credentials=credentials)
            self._initialized = True
            logger.info("Google Calendar API initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Calendar API: {e}")
            self._initialized = True
            
    def create_meeting(
        self,
        title: str,
        description: Optional[str] = None,
        start_time: Optional[datetime] = None,
        duration_minutes: int = 60,
        attendee_emails: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Create a Google Meet meeting.
        
        If Google API is configured, creates via Calendar API.
        Otherwise, returns a placeholder that teacher can fill with manual link.
        
        Returns:
            Dict with 'meeting_url', 'meeting_id', 'platform'
        """
        self._initialize()
        
        if not self.calendar_service:
            # No API configured - return template for manual link
            return {
                "meeting_url": None,
                "meeting_id": None,
                "platform": "google_meet",
                "requires_manual_link": True,
                "message": "Please create a Google Meet and paste the link"
            }
        
        try:
            # Create calendar event with Google Meet
            start = start_time or datetime.utcnow()
            end = start + timedelta(minutes=duration_minutes)
            
            event = {
                'summary': title,
                'description': description or '',
                'start': {
                    'dateTime': start.isoformat() + 'Z',
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end.isoformat() + 'Z',
                    'timeZone': 'UTC',
                },
                'conferenceData': {
                    'createRequest': {
                        'requestId': f"webinar-{int(datetime.now().timestamp())}",
                        'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                    }
                },
                'attendees': [{'email': email} for email in (attendee_emails or [])],
            }
            
            created_event = self.calendar_service.events().insert(
                calendarId='primary',
                body=event,
                conferenceDataVersion=1
            ).execute()
            
            meet_link = created_event.get('hangoutLink') or created_event.get('conferenceData', {}).get('entryPoints', [{}])[0].get('uri')
            
            return {
                "meeting_url": meet_link,
                "meeting_id": created_event.get('id'),
                "platform": "google_meet",
                "requires_manual_link": False,
                "calendar_event_id": created_event.get('id')
            }
            
        except Exception as e:
            logger.error(f"Failed to create Google Meet: {e}")
            return {
                "meeting_url": None,
                "meeting_id": None,
                "platform": "google_meet",
                "requires_manual_link": True,
                "error": str(e),
                "message": "Failed to auto-create. Please create manually and paste the link."
            }
    
    def generate_instant_meeting_link(self) -> str:
        """
        Generate a Google Meet link format.
        Note: This generates a valid-looking link but for actual meetings,
        you need to either:
        1. Use Calendar API (requires OAuth)
        2. Have the teacher create and paste the link manually
        """
        import random
        import string
        
        # Generate a random meeting code in Google Meet format (xxx-xxxx-xxx)
        def random_segment(length):
            return ''.join(random.choices(string.ascii_lowercase, k=length))
        
        code = f"{random_segment(3)}-{random_segment(4)}-{random_segment(3)}"
        return f"https://meet.google.com/{code}"
        
    def validate_meet_link(self, url: str) -> bool:
        """Validate if a URL is a valid Google Meet link"""
        if not url:
            return False
        return url.startswith("https://meet.google.com/") and len(url) > 25


# Singleton instance
google_meet_service = GoogleMeetService()
