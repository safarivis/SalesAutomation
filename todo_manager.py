import imaplib
import email
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
import time
from datetime import datetime, timedelta
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TodoManager:
    def __init__(self):
        load_dotenv()
        self.email_user = os.getenv('GMAIL_USER')
        self.email_password = os.getenv('GMAIL_APP_PASSWORD')
        self.daily_report_email = "louis@strijder.online"
        self.conn = sqlite3.connect('sales_automation.db')
        self.cursor = self.conn.cursor()
    
    def extract_todos(self, email_body):
        """Extract to-dos from email body using common patterns"""
        todos = []
        
        # More specific patterns for to-dos
        patterns = [
            r"(?i)(?:todo|to-do|to do|action item)[s]?[:]\s*(.*?)(?:\n|$)",
            r"(?i)(?:•|\*|\-|\d+\.)\s*(?:need to|please|must|should)\s*(.*?)(?:\n|$)",
            r"(?i)follow[- ]up[:]?\s*(.*?)(?:\n|$)",
            r"(?i)(?:please|kindly)\s+(?:can you|could you)?\s*(.*?)(?:\n|$)",
            r"(?i)(?:•|\*|\-|\d+\.)\s*([A-Z].*?(?:\.|\n|$))"  # Bullet points starting with capital letter
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, email_body)
            for match in matches:
                todo = match.group(1).strip()
                # Filter out noise
                if (todo and 
                    len(todo) > 10 and  # Ignore very short matches
                    not todo.startswith('http') and  # Ignore URLs
                    not re.match(r'^[\d\.\s]+$', todo) and  # Ignore number-only strings
                    not re.search(r'unsubscribe|privacy|terms', todo.lower())):  # Ignore common email footer text
                    todos.append(todo)
        
        return list(set(todos))  # Remove duplicates

    def save_todo(self, email_from, todo_text, message_id):
        """Save a to-do to the database"""
        try:
            self.cursor.execute("""
                INSERT INTO todos (email, todo_text, email_message_id)
                VALUES (?, ?, ?)
            """, (email_from, todo_text, message_id))
            self.conn.commit()
            logger.info(f"Saved todo: {todo_text}")
        except Exception as e:
            logger.error(f"Error saving todo: {str(e)}")

    def process_email(self, email_message):
        """Process a single email message for to-dos"""
        try:
            from_email = str(email_message['from'] or '')
            message_id = str(email_message['message-id'] or '')
            
            # Get email body
            body = ''
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
                        break
            else:
                body = email_message.get_payload(decode=True).decode()
            
            # Extract and save to-dos
            todos = self.extract_todos(body)
            for todo in todos:
                self.save_todo(from_email, todo, message_id)
            
            return True
        except Exception as e:
            logger.error(f"Error processing email: {str(e)}")
            return False

    def send_daily_summary(self):
        """Send daily summary of to-dos"""
        try:
            # Get all incomplete to-dos
            self.cursor.execute("""
                SELECT email, todo_text, created_at 
                FROM todos 
                WHERE completed = 0 
                ORDER BY created_at DESC
            """)
            todos = self.cursor.fetchall()
            
            if not todos:
                logger.info("No todos to report")
                return
            
            # Create email content
            subject = f"Daily To-Do Summary - {datetime.now().strftime('%Y-%m-%d')}"
            body = "Here are your current to-dos:\n\n"
            
            for email, todo, created_at in todos:
                body += f"• From {email} ({created_at}):\n  {todo}\n\n"
            
            # Create message
            message = MIMEMultipart()
            message["From"] = self.email_user
            message["To"] = self.daily_report_email
            message["Subject"] = subject
            message.attach(MIMEText(body, "plain"))
            
            # Send email
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(message)
            
            logger.info("Daily summary sent successfully")
            
        except Exception as e:
            logger.error(f"Error sending daily summary: {str(e)}")

    def monitor_and_process(self):
        """Monitor inbox for new emails and process them"""
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
                    logger.info("Successfully processed email for todos")
            
            mail.close()
            mail.logout()
            
        except Exception as e:
            logger.error(f"Error monitoring inbox: {str(e)}")

    def run(self):
        """Main run loop"""
        last_summary_date = None
        
        while True:
            try:
                # Check if we need to send daily summary
                current_date = datetime.now().date()
                if last_summary_date != current_date:
                    self.send_daily_summary()
                    last_summary_date = current_date
                
                # Monitor for new emails
                self.monitor_and_process()
                
                # Wait before next check
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in run loop: {str(e)}")
                time.sleep(60)  # Wait before retrying

if __name__ == "__main__":
    manager = TodoManager()
    manager.run()
