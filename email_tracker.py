import sqlite3
from datetime import datetime, timedelta
import uuid
from typing import Dict, List
import base64
from email.mime.image import MIMEImage
import os

class EmailTracker:
    def __init__(self, db_path: str = "sales.db"):
        self.db_path = db_path
        self.setup_database()
    
    def setup_database(self):
        """Set up the database tables for tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE,
            name TEXT,
            company TEXT,
            current_stage TEXT DEFAULT 'new',
            stage_updated_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS stages (
            id TEXT PRIMARY KEY,
            contact_id TEXT,
            stage TEXT,
            changed_from TEXT,
            changed_to TEXT,
            changed_at TIMESTAMP,
            FOREIGN KEY (contact_id) REFERENCES contacts(id)
        )''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_tracking (
            id TEXT PRIMARY KEY,
            recipient_email TEXT,
            subject TEXT,
            sent_time TIMESTAMP,
            opened BOOLEAN DEFAULT FALSE,
            opened_time TIMESTAMP,
            clicked BOOLEAN DEFAULT FALSE,
            clicked_time TIMESTAMP,
            responded BOOLEAN DEFAULT FALSE,
            responded_time TIMESTAMP,
            campaign_id TEXT,
            contact_id TEXT,
            FOREIGN KEY (contact_id) REFERENCES contacts(id)
        )''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS follow_ups (
            id TEXT PRIMARY KEY,
            original_email_id TEXT,
            sequence_number INTEGER,
            scheduled_time TIMESTAMP,
            sent BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (original_email_id) REFERENCES email_tracking(id)
        )''')
        
        conn.commit()
        conn.close()
    
    def generate_tracking_pixel(self, email_id: str) -> tuple:
        """Generate a tracking pixel for email opens"""
        tracking_pixel = MIMEImage(base64.b64decode(
            "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
        ))
        tracking_pixel.add_header('Content-ID', f'<tracking_pixel_{email_id}>')
        tracking_pixel.add_header('Content-Disposition', 'inline')
        
        return tracking_pixel, f'<img src="https://strijder.online/track/open/{email_id}" width="1" height="1" />'
    
    def add_tracking(self, email_content: str, email_id: str) -> str:
        """Add tracking elements to email content"""
        # Add tracking pixel
        _, pixel_html = self.generate_tracking_pixel(email_id)
        
        # Add click tracking to links, but exclude Calendly links
        modified_content = email_content
        for link in modified_content.split('href="')[1:]:
            original_url = link.split('"')[0]
            if 'calendly.com' not in original_url:
                modified_content = modified_content.replace(
                    f'href="{original_url}"',
                    f'href="https://strijder.online/track/click/{email_id}?url={original_url}"'
                )
        
        # Add tracking pixel before closing body tag
        modified_content = modified_content.replace('</body>', f'{pixel_html}</body>')
        
        return modified_content
    
    def schedule_follow_ups(self, email_id: str, recipient: str):
        """Schedule follow-up emails"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        follow_up_schedule = [
            (3, "Still interested in modernizing your practice?"),
            (7, "Quick update on practice automation"),
            (14, "One last thing about practice efficiency")
        ]
        
        for days_delay, subject in follow_up_schedule:
            follow_up_id = str(uuid.uuid4())
            scheduled_time = datetime.now() + timedelta(days=days_delay)
            
            cursor.execute('''
            INSERT INTO follow_ups (id, original_email_id, sequence_number, scheduled_time)
            VALUES (?, ?, ?, ?)
            ''', (follow_up_id, email_id, days_delay, scheduled_time))
        
        conn.commit()
        conn.close()
    
    def get_pending_follow_ups(self) -> List[Dict]:
        """Get follow-ups that need to be sent"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT f.id, f.original_email_id, f.sequence_number, e.recipient_email
        FROM follow_ups f
        JOIN email_tracking e ON f.original_email_id = e.id
        WHERE f.sent = FALSE 
        AND f.scheduled_time <= ?
        AND e.responded = FALSE
        ''', (datetime.now(),))
        
        follow_ups = []
        for row in cursor.fetchall():
            follow_ups.append({
                'id': row[0],
                'original_email_id': row[1],
                'sequence_number': row[2],
                'recipient_email': row[3]
            })
        
        conn.close()
        return follow_ups
    
    def mark_email_opened(self, email_id: str):
        """Mark an email as opened"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE email_tracking
        SET opened = TRUE, opened_time = ?
        WHERE id = ?
        ''', (datetime.now(), email_id))
        
        conn.commit()
        conn.close()
    
    def mark_email_clicked(self, email_id: str):
        """Mark an email as clicked"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE email_tracking
        SET clicked = TRUE, clicked_time = ?
        WHERE id = ?
        ''', (datetime.now(), email_id))
        
        conn.commit()
        conn.close()
    
    def mark_email_responded(self, email_id: str):
        """Mark an email as responded to"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE email_tracking
        SET responded = TRUE, responded_time = ?
        WHERE id = ?
        ''', (datetime.now(), email_id))
        
        conn.commit()
        conn.close()
    
    def update_contact_stage(self, email: str, new_stage: str):
        """Update contact's stage and record the change"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get or create contact
            cursor.execute('SELECT id, current_stage FROM contacts WHERE email = ?', (email,))
            result = cursor.fetchone()
            
            if result:
                contact_id, current_stage = result
            else:
                contact_id = str(uuid.uuid4())
                cursor.execute(
                    'INSERT INTO contacts (id, email, current_stage, stage_updated_at) VALUES (?, ?, ?, ?)',
                    (contact_id, email, new_stage, datetime.now())
                )
                current_stage = 'new'
            
            # Record stage change
            if current_stage != new_stage:
                stage_id = str(uuid.uuid4())
                cursor.execute(
                    'INSERT INTO stages (id, contact_id, stage, changed_from, changed_to, changed_at) VALUES (?, ?, ?, ?, ?, ?)',
                    (stage_id, contact_id, new_stage, current_stage, new_stage, datetime.now())
                )
                
                # Update contact's current stage
                cursor.execute(
                    'UPDATE contacts SET current_stage = ?, stage_updated_at = ? WHERE id = ?',
                    (new_stage, datetime.now(), contact_id)
                )
            
            conn.commit()
            return contact_id
            
        finally:
            conn.close()
