#!/usr/bin/env python3
"""
Quick Email Monitor - Streamlined version for real-time email monitoring
"""

import imaplib
import email
import sqlite3
import json
import os
import time
from datetime import datetime
from dotenv import load_dotenv
import logging
from email.header import decode_header
import threading
import queue

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QuickMonitor:
    def __init__(self):
        load_dotenv()
        self.email_queue = queue.Queue()
        self.db_path = 'sales_automation.db'
        self.email = os.getenv('GMAIL_USER')
        self.password = os.getenv('GMAIL_APP_PASSWORD')
        self.last_check_time = datetime.now()
        
        # Initialize IMAP connection
        self.setup_imap()
        
    def setup_imap(self):
        """Setup IMAP connection with auto-reconnect"""
        try:
            self.mail = imaplib.IMAP4_SSL('imap.gmail.com')
            self.mail.login(self.email, self.password)
            self.mail.select('INBOX')
            logger.info("IMAP connection established")
        except Exception as e:
            logger.error(f"IMAP connection failed: {e}")
            
    def check_new_emails(self):
        """Quick check for new emails"""
        try:
            # Search for new unread emails
            _, messages = self.mail.search(None, '(UNSEEN)')
            
            for num in messages[0].split():
                _, msg = self.mail.fetch(num, '(RFC822)')
                email_body = msg[0][1]
                email_message = email.message_from_bytes(email_body)
                
                # Extract email details
                subject = decode_header(email_message["subject"])[0][0]
                from_email = email.utils.parseaddr(email_message["from"])[1]
                date_str = email_message["date"]
                
                # Add to processing queue
                self.email_queue.put({
                    'from_email': from_email,
                    'subject': subject,
                    'date': date_str,
                    'message_id': email_message["message-id"],
                    'in_reply_to': email_message.get("in-reply-to", ""),
                    'body': self.get_email_body(email_message)
                })
                
                logger.info(f"New email from {from_email}: {subject}")
                
        except Exception as e:
            logger.error(f"Error checking emails: {e}")
            self.setup_imap()  # Try to reconnect
            
    def get_email_body(self, email_message):
        """Extract email body"""
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    return part.get_payload(decode=True).decode()
        else:
            return email_message.get_payload(decode=True).decode()
            
    def update_database(self, email_data):
        """Quick database update"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Update email status
                cursor.execute("""
                    UPDATE emails 
                    SET responded = 1, 
                        responded_at = ? 
                    WHERE to_email = ?
                """, (email_data['date'], email_data['from_email']))
                
                # Update contact stage if it's a reply
                if email_data['in_reply_to']:
                    # Check for keywords to determine stage
                    body_lower = email_data['body'].lower()
                    new_stage = 'responded'
                    
                    if 'calendly' in body_lower or 'schedule' in body_lower or 'book' in body_lower:
                        new_stage = 'demo_scheduled'
                    elif 'interested' in body_lower or 'tell me more' in body_lower:
                        new_stage = 'interested'
                    elif 'not interested' in body_lower or 'unsubscribe' in body_lower:
                        new_stage = 'not_interested'
                    
                    cursor.execute("""
                        UPDATE contacts 
                        SET current_stage = ?,
                            updated_at = ? 
                        WHERE email = ?
                    """, (new_stage, email_data['date'], email_data['from_email']))
                    
                    logger.info(f"Updated {email_data['from_email']} to stage: {new_stage}")
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Database error: {e}")
            
    def process_email_queue(self):
        """Process emails in the queue"""
        while True:
            try:
                email_data = self.email_queue.get(timeout=1)
                self.update_database(email_data)
                self.email_queue.task_done()
            except queue.Empty:
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error processing email: {e}")
                
    def run(self):
        """Main monitoring loop"""
        # Start email processing thread
        processing_thread = threading.Thread(target=self.process_email_queue, daemon=True)
        processing_thread.start()
        
        logger.info("Starting quick monitor...")
        
        while True:
            try:
                self.check_new_emails()
                # Quick status report
                if self.email_queue.qsize() > 0:
                    logger.info(f"Emails in queue: {self.email_queue.qsize()}")
                time.sleep(30)  # Check every 30 seconds
                
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                break
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                time.sleep(5)  # Wait before retrying

if __name__ == "__main__":
    monitor = QuickMonitor()
    monitor.run()
