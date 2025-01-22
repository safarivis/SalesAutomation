#!/usr/bin/env python3
"""
AI Sales Agent for Permission-Based Outreach
Implements Seth Godin-style email automation with Claude 3.5 integration
"""

import os
import ssl
import json
import email
import sqlite3
import smtplib
import imaplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import anthropic
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='sales_agent.log'
)
logger = logging.getLogger(__name__)

class SalesAgent:
    def __init__(self, config_path: str = "config.json"):
        """Initialize the sales agent with configuration"""
        self.config = self._load_config(config_path)
        self.claude_client = anthropic.Client(api_key=self.config["anthropic_api_key"])
        self.db_conn = self._init_database()
        self.email_tracker = EmailTracker()
        self.calendly = CalendlyIntegration()
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(config_path) as f:
                return json.load(f)
        except FileNotFoundError:
            raise Exception(f"Configuration file not found at {config_path}")

    def _init_database(self) -> sqlite3.Connection:
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.config["database_path"])
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS contacts (
                email TEXT PRIMARY KEY,
                name TEXT,
                industry TEXT,
                last_contacted TEXT,
                created_at TEXT
            );
            
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_email TEXT,
                type TEXT,
                content TEXT,
                timestamp TEXT,
                FOREIGN KEY (contact_email) REFERENCES contacts(email)
            );
            
            CREATE TABLE IF NOT EXISTS unsubscribes (
                email TEXT PRIMARY KEY,
                timestamp TEXT,
                reason TEXT
            );
            
            CREATE TABLE IF NOT EXISTS leads (
                email TEXT PRIMARY KEY,
                status TEXT,
                last_updated TEXT
            );
        """)
        conn.commit()
        return conn

    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send email via Gmail SMTP"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config["gmail_user"]
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # TODO: Implement DKIM signing
            # TODO: Add SPF record verification
            
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                server.login(self.config["gmail_user"], self.config["gmail_app_password"])
                server.send_message(msg)
                
            self._log_interaction(to_email, "sent_email", body)
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def check_replies(self) -> List[Dict]:
        """Check for new replies via IMAP"""
        try:
            replies = []
            with imaplib.IMAP4_SSL("imap.gmail.com") as imap:
                imap.login(self.config["gmail_user"], self.config["gmail_app_password"])
                imap.select("INBOX")
                
                # Search for unread messages
                _, messages = imap.search(None, "UNSEEN")
                
                for msg_num in messages[0].split():
                    _, msg_data = imap.fetch(msg_num, "(RFC822)")
                    email_body = msg_data[0][1]
                    message = email.message_from_bytes(email_body)
                    
                    reply = {
                        "from": email.utils.parseaddr(message["from"])[1],
                        "subject": message["subject"],
                        "body": self._get_email_body(message),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    replies.append(reply)
                    self._log_interaction(reply["from"], "received_reply", reply["body"])
                    
                    # Check for unsubscribe requests
                    if "STOP" in reply["body"].upper():
                        self._handle_unsubscribe(reply["from"])
                        
            return replies
            
        except Exception as e:
            logger.error(f"Failed to check replies: {str(e)}")
            return []

    def _get_email_body(self, message: email.message.Message) -> str:
        """Extract email body from message"""
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() == "text/plain":
                    return part.get_payload(decode=True).decode()
        return message.get_payload(decode=True).decode()

    def generate_response(self, incoming_email: Dict) -> Optional[str]:
        """Generate response using Claude 3.5"""
        try:
            prompt = self._create_claude_prompt(incoming_email)
            response = self.claude_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                temperature=0.7,
                system="""You are an empathetic sales assistant. Generate helpful, 
                         story-driven responses following Seth Godin's philosophy. 
                         Be concise, genuine, and always respect opt-out requests.""",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Failed to generate Claude response: {str(e)}")
            return None

    def _create_claude_prompt(self, incoming_email: Dict) -> str:
        """Create context-aware prompt for Claude"""
        return f"""
        Incoming email from: {incoming_email['from']}
        Subject: {incoming_email['subject']}
        Body: {incoming_email['body']}
        
        Previous interactions from database:
        {self._get_previous_interactions(incoming_email['from'])}
        
        Generate an appropriate response following Seth Godin's philosophy:
        - Start with a relevant story or observation
        - Be genuinely helpful
        - Respect the reader's time
        - Include clear value proposition
        """

    def _log_interaction(self, email: str, interaction_type: str, content: str) -> None:
        """Log interaction to SQLite database"""
        cursor = self.db_conn.cursor()
        cursor.execute("""
            INSERT INTO interactions (contact_email, type, content, timestamp)
            VALUES (?, ?, ?, ?)
        """, (email, interaction_type, content, datetime.now().isoformat()))
        self.db_conn.commit()

    def _handle_unsubscribe(self, email: str) -> None:
        """Process unsubscribe request"""
        cursor = self.db_conn.cursor()
        cursor.execute("""
            INSERT INTO unsubscribes (email, timestamp, reason)
            VALUES (?, ?, ?)
        """, (email, datetime.now().isoformat(), "User replied STOP"))
        self.db_conn.commit()
        logger.info(f"User {email} has been unsubscribed")

    def _get_previous_interactions(self, email: str) -> List[Dict]:
        """Retrieve previous interactions for a contact"""
        cursor = self.db_conn.cursor()
        cursor.execute("""
            SELECT type, content, timestamp 
            FROM interactions 
            WHERE contact_email = ? 
            ORDER BY timestamp DESC 
            LIMIT 5
        """, (email,))
        return cursor.fetchall()

    def handle_calendly_event(self, event_data: dict):
        """Handle Calendly webhook events"""
        event_type = event_data.get('event')
        
        if event_type == 'invitee.created':
            # Someone booked a demo
            invitee = event_data['payload']['invitee']
            email = invitee['email']
            name = invitee['name']
            event_time = invitee['event']['start_time']
            
            # Send confirmation email
            self.send_booking_confirmation(email, name, event_time)
            
            # Update CRM/database
            self.update_lead_status(email, 'demo_scheduled')
            
        elif event_type == 'invitee.canceled':
            # Someone canceled their demo
            invitee = event_data['payload']['invitee']
            email = invitee['email']
            
            # Send follow-up email
            self.send_cancellation_follow_up(email)
            
            # Update CRM/database
            self.update_lead_status(email, 'demo_canceled')
    
    def send_booking_confirmation(self, email: str, name: str, event_time: str):
        """Send a confirmation email for the demo booking"""
        subject = "Demo Confirmed - AI Practice Solutions"
        
        content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <p>Hi {name},</p>
            
            <p>Thank you for scheduling a demo of our AI Practice Solutions! I'm looking forward to showing you how we can help modernize your practice.</p>
            
            <p>Your demo is scheduled for: <strong>{event_time}</strong></p>
            
            <p>To help me prepare, could you please take a moment to:</p>
            <ol>
                <li>Confirm your current practice management software</li>
                <li>Note any specific challenges you'd like to address</li>
            </ol>
            
            <p>Just reply to this email with those details.</p>
            
            <p>Best regards,<br>
            Louis du Plessis</p>
        </body>
        </html>
        """
        
        self.email_tracker.send_email(email, subject, content)
    
    def send_cancellation_follow_up(self, email: str):
        """Send a follow-up email when someone cancels their demo"""
        subject = "Sorry we missed you - Reschedule your AI Practice Demo"
        
        content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <p>Hi there,</p>
            
            <p>I noticed you canceled your demo of our AI Practice Solutions. I understand that schedules can be busy!</p>
            
            <p>Would you like to reschedule for a more convenient time? You can book directly here:</p>
            
            <p><a href="{self.calendly.get_booking_url()}" style="display: inline-block; background-color: #2c5282; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reschedule Demo</a></p>
            
            <p>Or if there's something specific you'd like to discuss first, just reply to this email.</p>
            
            <p>Best regards,<br>
            Louis du Plessis</p>
        </body>
        </html>
        """
        
        self.email_tracker.send_email(email, subject, content)
    
    def update_lead_status(self, email: str, status: str):
        """Update lead status in database"""
        cursor = self.db_conn.cursor()
        
        cursor.execute('''
            UPDATE leads
            SET status = ?, last_updated = ?
            WHERE email = ?
        ''', (status, datetime.now().isoformat(), email))
        
        self.db_conn.commit()
    
    def get_upcoming_demos(self) -> List[Dict]:
        """Get list of upcoming demos"""
        return self.calendly.get_scheduled_events(
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(days=7)
        )
    
    def __del__(self):
        """Cleanup database connection"""
        if hasattr(self, 'db_conn'):
            self.db_conn.close()

if __name__ == "__main__":
    agent = SalesAgent()
    # Main execution logic would go here
