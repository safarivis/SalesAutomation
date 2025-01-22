from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, List, Dict
import smtplib
import os
from dotenv import load_dotenv
import json
import sqlite3
from datetime import datetime
import logging
import uuid
from email_tracker import EmailTracker
from mailgun_manager import MailgunManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailSender:
    def __init__(self, config_path: str = "config.json"):
        load_dotenv()
        with open(config_path) as f:
            self.config = json.load(f)
        
        # Email settings
        self.email_user = os.getenv('EMAIL_USER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.hostinger.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '465'))
        
        if not self.email_user or not self.email_password:
            raise ValueError("Email credentials not found in environment variables")
        
        # Initialize tracker
        self.tracker = EmailTracker()
        self.mailgun = MailgunManager()
    
    def send_email(self, to_email: str, subject: str, content: str, campaign_id: Optional[str] = None) -> bool:
        """Send an email with tracking capabilities"""
        try:
            # Generate unique email ID for tracking
            email_id = str(uuid.uuid4())
            
            # Add tracking elements
            tracked_content = self.tracker.add_tracking(content, email_id)
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_user
            msg['To'] = to_email
            
            # Attach HTML version
            msg.attach(MIMEText(tracked_content, 'html'))
            
            # Send email
            try:
                if self.smtp_port == 587:  # TLS
                    with smtplib.SMTP(self.smtp_server, self.smtp_port) as smtp:
                        smtp.starttls()
                        smtp.login(self.email_user, self.email_password)
                        smtp.send_message(msg)
                else:  # SSL
                    with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as smtp:
                        smtp.login(self.email_user, self.email_password)
                        smtp.send_message(msg)
                logger.info(f"Email sent successfully to {to_email}")
                return True
            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"SMTP Authentication failed: {str(e)}")
                return False
            except Exception as e:
                logger.error(f"Failed to send email: {str(e)}")
                return False
            
            # Log email in tracking database
            conn = sqlite3.connect(self.config.get("database_path", "sales.db"))
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO email_tracking 
                (id, recipient_email, subject, sent_time, campaign_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (email_id, to_email, subject, datetime.now(), campaign_id))
            
            conn.commit()
            conn.close()
            
            # Schedule follow-ups
            self.tracker.schedule_follow_ups(email_id, to_email)
            
            logger.info(f"Email sent successfully to {to_email} with tracking ID {email_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            logger.error(f"Full error: {type(e).__name__}: {str(e)}")
            return False
    
    def send_email_mailgun(self, to_email: str, subject: str, html_content: str, 
                  tags: List[str] = None, variables: Dict = None) -> Optional[str]:
        """
        Send an email using Mailgun
        Returns message_id if successful, None if failed
        """
        return self.mailgun.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            tags=tags,
            variables=variables
        )
    
    def send_follow_ups(self):
        """Send any pending follow-up emails"""
        pending_follow_ups = self.tracker.get_pending_follow_ups()
        
        for follow_up in pending_follow_ups:
            # Generate follow-up content based on sequence number
            content = self.generate_follow_up_content(follow_up['sequence_number'])
            
            # Send follow-up
            success = self.send_email(
                to_email=follow_up['recipient_email'],
                subject=f"Re: AI Practice Solutions - Follow-up #{follow_up['sequence_number']}",
                content=content
            )
            
            if success:
                # Mark follow-up as sent
                conn = sqlite3.connect(self.config.get("database_path", "sales.db"))
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE follow_ups
                    SET sent = TRUE
                    WHERE id = ?
                ''', (follow_up['id'],))
                conn.commit()
                conn.close()
    
    def generate_follow_up_content(self, sequence_number: int) -> str:
        """Generate content for follow-up emails"""
        if sequence_number == 3:
            return """
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <p>I wanted to follow up on my previous email about modernizing your medical practice.</p>
                
                <p>Many practices we work with were initially hesitant about implementing AI solutions, but after seeing a demo, they were amazed by how simple and effective it is.</p>
                
                <p>Would you be interested in a quick 5-minute demo?</p>
                
                <p>Best regards,<br>
                Louis du Plessis</p>
            </body>
            </html>
            """
        elif sequence_number == 7:
            return """
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <p>I thought you might be interested in some recent results from our medical practice clients:</p>
                
                <ul>
                    <li>60% reduction in phone calls</li>
                    <li>40% fewer missed appointments</li>
                    <li>24/7 patient support without additional staff</li>
                </ul>
                
                <p>Would you like to see how we achieved these results?</p>
                
                <p>Best regards,<br>
                Louis du Plessis</p>
            </body>
            </html>
            """
        else:  # sequence_number == 14
            return """
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <p>I'll keep this brief - this is my final follow-up.</p>
                
                <p>If you're still interested in modernizing your practice with AI solutions, our offer for a free demo still stands.</p>
                
                <p>Just reply to this email, and I'll take care of the rest.</p>
                
                <p>Best regards,<br>
                Louis du Plessis</p>
            </body>
            </html>
            """

if __name__ == "__main__":
    # Example usage
    sender = EmailSender()
    test_email = "test@example.com"
    
    # Send test email
    content = """
    <html>
    <body>
    <p>Hello,</p>
    <p>This is a test email with tracking capabilities.</p>
    <p>Click <a href="http://example.com">here</a> to visit our website.</p>
    </body>
    </html>
    """
    
    success = sender.send_email(test_email, "Test Email", content)
    if success:
        print(f"Test email sent successfully to {test_email}")
        sender.send_follow_ups()
    else:
        print("Failed to send test email")
