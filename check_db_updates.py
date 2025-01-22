import sqlite3
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from tabulate import tabulate

load_dotenv()

def check_recent_updates():
    conn = sqlite3.connect('sales_automation.db')
    cursor = conn.cursor()
    
    print("\n=== Recent Contact Stage Updates ===")
    cursor.execute("""
        SELECT email, current_stage, updated_at 
        FROM contacts 
        ORDER BY updated_at DESC 
        LIMIT 5
    """)
    contacts = cursor.fetchall()
    print(tabulate(contacts, headers=['Email', 'Current Stage', 'Updated At'], tablefmt='grid'))
    
    print("\n=== Recent Email Responses ===")
    cursor.execute("""
        SELECT message_id, to_email, subject, responded, sent_at 
        FROM emails 
        WHERE responded = 1
        ORDER BY sent_at DESC 
        LIMIT 5
    """)
    emails = cursor.fetchall()
    print(tabulate(emails, headers=['Message ID', 'To Email', 'Subject', 'Responded', 'Sent At'], tablefmt='grid'))
    
    print("\n=== Stage Change History ===")
    cursor.execute("""
        SELECT email, old_stage, new_stage, changed_at 
        FROM stages 
        ORDER BY changed_at DESC 
        LIMIT 5
    """)
    stages = cursor.fetchall()
    print(tabulate(stages, headers=['Email', 'Old Stage', 'New Stage', 'Changed At'], tablefmt='grid'))
    
    conn.close()

if __name__ == "__main__":
    check_recent_updates()
