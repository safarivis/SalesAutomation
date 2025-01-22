from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
import pickle
from typing import Optional, List, Dict
import base64
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.labels'
]

class GmailManager:
    def __init__(self):
        self.credentials_dir = Path('.credentials')
        self.service_account_path = self.credentials_dir / 'service-account.json'
        self.gmail_user = os.getenv('GMAIL_USER')
        
        self.creds = self._get_credentials()
        self.service = build('gmail', 'v1', credentials=self.creds)
        self.labels = self._setup_labels()
        self.tracker = EmailTracker()
        
        # Map Gmail labels to database stages
        self.label_to_stage = {
            'responses': 'responded',
            'scheduled': 'demo_scheduled',
            'interested': 'interested',
            'not_interested': 'not_interested'
        }
    
    def _get_credentials(self):
        """Get credentials from service account"""
        if not self.service_account_path.exists():
            raise FileNotFoundError(
                f"Service account key file not found at {self.service_account_path}. "
                "Please download it from Google Cloud Console and place it in the .credentials directory."
            )
        
        credentials = service_account.Credentials.from_service_account_file(
            str(self.service_account_path),
            scopes=SCOPES
        )
        
        # Create delegated credentials for the Gmail user
        delegated_credentials = credentials.with_subject(self.gmail_user)
        return delegated_credentials
    
    def _setup_labels(self) -> Dict[str, str]:
        """Setup required Gmail labels"""
        label_names = {
            'base': 'Sales Outreach',
            'responses': 'Sales Outreach/Responses',
            'scheduled': 'Sales Outreach/Scheduled Demos',
            'interested': 'Sales Outreach/Interested',
            'not_interested': 'Sales Outreach/Not Interested'
        }
        
        created_labels = {}
        existing_labels = self.service.users().labels().list(userId='me').execute().get('labels', [])
        existing_label_names = {label['name']: label['id'] for label in existing_labels}
        
        for key, name in label_names.items():
            if name not in existing_label_names:
                label_object = {
                    'name': name,
                    'labelListVisibility': 'labelShow',
                    'messageListVisibility': 'show'
                }
                created_label = self.service.users().labels().create(
                    userId='me',
                    body=label_object
                ).execute()
                created_labels[key] = created_label['id']
            else:
                created_labels[key] = existing_label_names[name]
        
        return created_labels
    
    def move_to_label(self, message_id: str, label_key: str):
        """Move an email to a specific label"""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={
                    'addLabelIds': [self.labels[label_key]],
                    'removeLabelIds': ['INBOX']
                }
            ).execute()
            logger.info(f"Moved message {message_id} to label {label_key}")
        except Exception as e:
            logger.error(f"Error moving message to label: {str(e)}")
    
    def classify_email(self, email_data: Dict) -> str:
        """Classify email and return appropriate label key"""
        subject = email_data['subject'].lower()
        body = email_data['body'].lower()
        
        # Check for demo scheduling confirmation
        if 'calendly' in body or 'scheduled' in body or 'appointment' in body:
            return 'scheduled'
        
        # Check for positive responses
        positive_keywords = ['interested', 'would like to learn', 'tell me more', 'demo']
        if any(keyword in body for keyword in positive_keywords):
            return 'interested'
        
        # Check for negative responses
        negative_keywords = ['not interested', 'unsubscribe', 'remove me', 'no thank you']
        if any(keyword in body for keyword in negative_keywords):
            return 'not_interested'
        
        # Default to responses for any other reply
        return 'responses'
    
    def process_incoming_email(self, email_data: Dict):
        """Process incoming email and organize into appropriate label"""
        # Get message ID from email data
        message_id = email_data['message_id']
        
        # Classify email
        label_key = self.classify_email(email_data)
        
        # Move to appropriate label
        self.move_to_label(message_id, label_key)
        
        # Update contact stage in database
        if label_key in self.label_to_stage:
            stage = self.label_to_stage[label_key]
            self.tracker.update_contact_stage(email_data['from'], stage)
        
        return label_key

if __name__ == "__main__":
    # Test the Gmail manager
    gmail = GmailManager()
    print("Available labels:", gmail.labels)
