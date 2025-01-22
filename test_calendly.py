from calendly_integration import CalendlyIntegration
from datetime import datetime, timedelta

def test_calendly_connection():
    """Test Calendly API connection and functionality"""
    calendly = CalendlyIntegration()
    
    # Get current user
    print("\nGetting current user...")
    user = calendly.get_current_user()
    print(f"Current user: {user.get('name', 'Unknown')} ({user.get('email', 'Unknown')})")
    
    # Get event types
    print("\nGetting event types...")
    event_types = calendly.get_event_types()
    print(f"Found {len(event_types)} event types")
    for event_type in event_types:
        print(f"- {event_type['name']} ({event_type['slug']})")
    
    # Get upcoming events
    print("\nGetting upcoming events...")
    events = calendly.get_scheduled_events()
    print(f"Found {len(events)} upcoming events")
    
    # Get booking URL
    print("\nGetting booking URL...")
    booking_url = calendly.get_booking_url("ai-practice-demo")
    print(f"Booking URL: {booking_url}")

if __name__ == "__main__":
    test_calendly_connection()
