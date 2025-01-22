#!/usr/bin/env python3
import imaplib
import email
import os
from datetime import datetime
from dotenv import load_dotenv

def check_responses():
    load_dotenv()
    
    # Gmail credentials
    EMAIL = os.getenv('GMAIL_USER')
    PASSWORD = os.getenv('GMAIL_APP_PASSWORD')
    
    try:
        # Connect to Gmail
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(EMAIL, PASSWORD)
        mail.select('INBOX')
        
        # Search for responses
        _, messages = mail.search(None, '(FROM "louisrdup@gmail.com")')
        
        if not messages[0]:
            print("No responses found from louisrdup@gmail.com")
            return
        
        # Process messages
        for num in messages[0].split():
            _, msg = mail.fetch(num, '(RFC822)')
            email_body = msg[0][1]
            email_message = email.message_from_bytes(email_body)
            
            print("\nFound response:")
            print(f"Date: {email_message['date']}")
            print(f"Subject: {email_message['subject']}")
            print(f"From: {email_message['from']}")
            print("\nContent:")
            
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        print(part.get_payload(decode=True).decode())
                        break
            else:
                print(email_message.get_payload(decode=True).decode())
        
        mail.close()
        mail.logout()
        
    except Exception as e:
        print(f"Error checking responses: {str(e)}")

if __name__ == "__main__":
    check_responses()
