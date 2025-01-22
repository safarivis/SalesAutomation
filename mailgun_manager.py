import os
import requests
import json
from typing import Optional, List, Dict
from datetime import datetime
import logging
from email_tracker import EmailTracker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MailgunManager:
    def __init__(self):
        self.domain = os.getenv('MAILGUN_DOMAIN')
        self.api_key = os.getenv('MAILGUN_API_KEY')
        self.base_url = f"https://api.mailgun.net/v3/{self.domain}"
        self.from_email = os.getenv('MAILGUN_FROM_EMAIL')
        self.tracker = EmailTracker()

    def send_email(self, to_email: str, subject: str, html_content: str, 
                  tags: List[str] = None, variables: Dict = None) -> Optional[str]:
        """
        Send an email using Mailgun
        Returns message_id if successful, None if failed
        """
        try:
            data = {
                'from': self.from_email,
                'to': to_email,
                'subject': subject,
                'html': html_content,
                'o:tracking': 'yes',
                'o:tracking-clicks': 'yes',
                'o:tracking-opens': 'yes',
                'h:Reply-To': self.from_email,
            }

            # Add custom variables for tracking
            if variables:
                for key, value in variables.items():
                    data[f'v:{key}'] = value

            # Add tags for better organization
            if tags:
                data['o:tag'] = tags

            response = requests.post(
                f"{self.base_url}/messages",
                auth=("api", self.api_key),
                data=data
            )
            response.raise_for_status()

            # Extract message ID from response
            message_id = response.json()['id']
            
            # Track the sent email
            self.tracker.track_email_sent(
                message_id=message_id,
                to_email=to_email,
                subject=subject,
                sent_at=datetime.now()
            )

            logger.info(f"Email sent successfully to {to_email}")
            return message_id

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return None

    def process_webhook(self, event_data: dict):
        """
        Process Mailgun webhook events
        """
        try:
            event_type = event_data.get('event')
            message_id = event_data.get('message', {}).get('headers', {}).get('message-id')
            
            if not message_id:
                logger.warning("No message ID in webhook data")
                return

            if event_type == 'opened':
                self.tracker.mark_email_opened(message_id)
                logger.info(f"Marked email {message_id} as opened")

            elif event_type == 'clicked':
                self.tracker.mark_email_clicked(message_id)
                logger.info(f"Marked email {message_id} as clicked")

            elif event_type == 'failed':
                reason = event_data.get('reason', 'unknown')
                self.tracker.mark_email_failed(message_id, reason)
                logger.warning(f"Email {message_id} failed: {reason}")

            elif event_type == 'delivered':
                self.tracker.mark_email_delivered(message_id)
                logger.info(f"Marked email {message_id} as delivered")

        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")

    def process_inbound_email(self, email_data: dict):
        """
        Process inbound emails from Mailgun
        """
        try:
            # Extract relevant data
            from_email = email_data.get('from')
            subject = email_data.get('subject')
            body_html = email_data.get('body-html')
            body_plain = email_data.get('body-plain')
            message_id = email_data.get('Message-Id')
            in_reply_to = email_data.get('In-Reply-To')
            
            # If it's a reply, mark the original email as responded
            if in_reply_to:
                self.tracker.mark_email_responded(in_reply_to)
                logger.info(f"Marked email {in_reply_to} as responded")

            # Analyze response sentiment
            body = body_plain or ''
            if any(word in body.lower() for word in ['interested', 'demo', 'learn more']):
                self.tracker.update_contact_stage(from_email, 'interested')
            elif any(word in body.lower() for word in ['not interested', 'unsubscribe']):
                self.tracker.update_contact_stage(from_email, 'not_interested')
            elif 'calendly' in body.lower():
                self.tracker.update_contact_stage(from_email, 'demo_scheduled')
            else:
                self.tracker.update_contact_stage(from_email, 'responded')

            logger.info(f"Processed inbound email from {from_email}")

        except Exception as e:
            logger.error(f"Error processing inbound email: {str(e)}")

    def get_email_stats(self, days: int = 30) -> Dict:
        """
        Get email statistics for the specified number of days
        """
        try:
            response = requests.get(
                f"{self.base_url}/stats/total",
                auth=("api", self.api_key),
                params={
                    'event': ['accepted', 'delivered', 'failed', 'opened', 'clicked'],
                    'duration': f"{days}d"
                }
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Failed to get email stats: {str(e)}")
            return {}
