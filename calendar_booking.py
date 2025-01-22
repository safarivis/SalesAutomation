from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import datetime
import os.path
import pickle

class CalendarBooking:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/calendar']
        self.creds = None
        
    def authenticate(self):
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                self.creds = flow.run_local_server(port=0)
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)
        
        self.service = build('calendar', 'v3', credentials=self.creds)
    
    def create_booking_link(self, email: str) -> str:
        """Create a unique booking link for a prospect"""
        # Generate a unique meeting link using Google Calendar API
        event = {
            'summary': 'AI Practice Solutions Demo',
            'description': 'See how our AI solutions can transform your medical practice',
            'start': {
                'dateTime': '2024-01-23T10:00:00+02:00',
                'timeZone': 'Africa/Johannesburg',
            },
            'end': {
                'dateTime': '2024-01-23T10:30:00+02:00',
                'timeZone': 'Africa/Johannesburg',
            },
            'attendees': [
                {'email': email}
            ],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 30},
                ],
            },
        }
        
        # Get available time slots
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = self.service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        return f"https://calendar.google.com/calendar/appointments/schedules/{self.creds.id}"
