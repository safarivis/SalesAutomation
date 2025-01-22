import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('sales_automation.db')
    cursor = conn.cursor()
    
    # Create contacts table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contacts (
        email TEXT PRIMARY KEY,
        current_stage TEXT,
        updated_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create emails table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS emails (
        message_id TEXT PRIMARY KEY,
        from_email TEXT,
        to_email TEXT,
        subject TEXT,
        sent_at TIMESTAMP,
        responded BOOLEAN DEFAULT 0,
        responded_at TIMESTAMP
    )
    """)
    
    # Create stages table for tracking stage changes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        old_stage TEXT,
        new_stage TEXT,
        changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create todos table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS todos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        todo_text TEXT,
        completed BOOLEAN DEFAULT 0,
        due_date TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        email_message_id TEXT,
        FOREIGN KEY(email_message_id) REFERENCES emails(message_id)
    )
    """)
    
    # Insert some test data
    cursor.execute("INSERT OR IGNORE INTO contacts (email, current_stage, updated_at) VALUES (?, ?, ?)",
                  ("test@example.com", "interested", datetime.now()))
    
    cursor.execute("INSERT OR IGNORE INTO emails (message_id, to_email, subject, sent_at, responded) VALUES (?, ?, ?, ?, ?)",
                  ("<test123@mail.gmail.com>", "test@example.com", "Your sales outreach", datetime.now(), 1))
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_db()
