import imaplib
import email
from email.header import decode_header
import os
from dotenv import load_dotenv
import time
import logging
from email_tracker import EmailTracker
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailMonitor:
    def __init__(self):
        load_dotenv()
        self.email_user = os.getenv('GMAIL_USER')
        self.email_password = os.getenv('GMAIL_APP_PASSWORD')
        self.tracker = EmailTracker()
    
    def process_email(self, email_message):
        """Process a single email message"""
        try:
            # Get email details
            subject = str(email_message['subject'] or '')
            from_email = str(email_message['from'] or '')
            message_id = str(email_message['message-id'] or '')
            in_reply_to = str(email_message.get('in-reply-to', ''))
            
            # Get email body
            body = ''
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
                        break
            else:
                body = email_message.get_payload(decode=True).decode()
            
            # If it's a reply to one of our emails
            if in_reply_to:
                self.tracker.mark_email_responded(in_reply_to)
                logger.info(f"Marked email {in_reply_to} as responded")
                
                # Analyze response
                body_lower = body.lower()
                if any(word in body_lower for word in ['interested', 'demo', 'learn more', 'schedule']):
                    self.tracker.update_contact_stage(from_email, 'interested')
                elif any(word in body_lower for word in ['not interested', 'unsubscribe', 'remove']):
                    self.tracker.update_contact_stage(from_email, 'not_interested')
                elif 'calendly' in body_lower:
                    self.tracker.update_contact_stage(from_email, 'demo_scheduled')
                else:
                    self.tracker.update_contact_stage(from_email, 'responded')
                
                logger.info(f"Updated stage for {from_email}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing email: {str(e)}")
            return False
    
    def monitor_inbox(self):
        """Monitor inbox for new emails"""
        while True:
            try:
                # Connect to Gmail
                mail = imaplib.IMAP4_SSL('imap.gmail.com')
                mail.login(self.email_user, self.email_password)
                mail.select('INBOX')
                
                # Search for unread emails
                _, messages = mail.search(None, 'UNSEEN')
                
                for num in messages[0].split():
                    # Fetch email message
                    _, msg = mail.fetch(num, '(RFC822)')
                    email_body = msg[0][1]
                    email_message = email.message_from_bytes(email_body)
                    
                    if self.process_email(email_message):
                        logger.info("Successfully processed email")
                    
                mail.close()
                mail.logout()
                
            except Exception as e:
                logger.error(f"Error monitoring inbox: {str(e)}")
            
            # Wait before checking again
            time.sleep(60)  # Check every minute

if __name__ == "__main__":
    monitor = EmailMonitor()
    monitor.monitor_inbox()
