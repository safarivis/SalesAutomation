#!/usr/bin/env python3
"""
Database cleanup script for Sales Automation System
"""

import sqlite3
import json
from datetime import datetime

def load_config(config_path: str = "config.json"):
    with open(config_path) as f:
        return json.load(f)

def cleanup_duplicates():
    config = load_config()
    conn = sqlite3.connect(config["database_path"])
    cursor = conn.cursor()
    
    # Create temporary table with unique interactions
    cursor.execute("""
        CREATE TEMPORARY TABLE temp_interactions AS
        SELECT MIN(id) as id, contact_email, type, content, MIN(timestamp) as timestamp
        FROM interactions
        GROUP BY contact_email, type, content
    """)
    
    # Delete all records from original table
    cursor.execute("DELETE FROM interactions")
    
    # Insert unique records back
    cursor.execute("""
        INSERT INTO interactions (contact_email, type, content, timestamp)
        SELECT contact_email, type, content, timestamp
        FROM temp_interactions
        ORDER BY timestamp
    """)
    
    # Drop temporary table
    cursor.execute("DROP TABLE temp_interactions")
    
    # Get count of removed duplicates
    cursor.execute("SELECT COUNT(*) FROM interactions")
    final_count = cursor.fetchone()[0]
    
    conn.commit()
    conn.close()
    
    return final_count

if __name__ == "__main__":
    print("Cleaning up duplicate interactions...")
    count = cleanup_duplicates()
    print(f"Cleanup complete. {count} unique interactions remain.")
