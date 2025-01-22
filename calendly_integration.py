import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

class CalendlyIntegration:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv('CALENDLY_API_KEY')
        self.base_url = "https://api.calendly.com/v2"
        self.booking_url = "https://calendly.com/louisrdup"
        
        if not self.api_key:
            raise ValueError("Calendly API key is required")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def get_booking_url(self, event_type: str = "ai-practice-demo") -> str:
        """Get the booking URL for a specific event type"""
        return f"{self.booking_url}/{event_type}"
    
    def get_current_user(self) -> Dict:
        """Get current user details using /users/me endpoint"""
        url = f"{self.base_url}/users/me"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()["resource"]
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get current user: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            return {}
    
    def get_event_types(self) -> List[Dict]:
        """Get all event types for the current user"""
        # First get the current user
        user = self.get_current_user()
        if not user:
            logger.error("Could not get current user")
            return []
        
        url = f"{self.base_url}/event_types"
        params = {
            "user": user["uri"],
            "active": "true"  # Only get active event types
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()["collection"]
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get event types: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            return []
    
    def get_scheduled_events(self, start_time: Optional[datetime] = None, 
                           end_time: Optional[datetime] = None,
                           status: str = "active") -> List[Dict]:
        """Get all scheduled events for the current user"""
        # First get the current user
        user = self.get_current_user()
        if not user:
            logger.error("Could not get current user")
            return []
        
        if not start_time:
            start_time = datetime.now()
        if not end_time:
            end_time = start_time + timedelta(days=30)
        
        url = f"{self.base_url}/scheduled_events"
        params = {
            "user": user["uri"],
            "min_start_time": start_time.isoformat(),
            "max_start_time": end_time.isoformat(),
            "status": status
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()["collection"]
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get scheduled events: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            return []
    
    def get_event_invitees(self, event_uuid: str) -> List[Dict]:
        """Get all invitees for a specific event"""
        url = f"{self.base_url}/scheduled_events/{event_uuid}/invitees"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()["collection"]
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get invitees: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            return []

def get_demo_booking_url() -> str:
    """Get the demo booking URL"""
    return "https://calendly.com/louisrdup/ai-practice-demo"

if __name__ == "__main__":
    # Test the Calendly integration
    calendly = CalendlyIntegration()
    
    print("\nGetting current user...")
    user = calendly.get_current_user()
    print(f"Current user: {user.get('name', 'Unknown')} ({user.get('email', 'Unknown')})")
    
    print("\nGetting event types...")
    event_types = calendly.get_event_types()
    print(f"Found {len(event_types)} event types")
    for event_type in event_types:
        print(f"- {event_type['name']} ({event_type['slug']})")
    
    print("\nGetting upcoming events...")
    events = calendly.get_scheduled_events()
    print(f"Found {len(events)} upcoming events")
    
    print("\nBooking URL for AI Practice Demo:")
    print(calendly.get_booking_url("ai-practice-demo"))
