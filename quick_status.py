#!/usr/bin/env python3
"""
Quick Status Checker - Get prospect status instantly
Usage: python quick_status.py [email]
"""

import sqlite3
import sys
import json
from datetime import datetime
import argparse

def get_prospect_status(email):
    """Get quick status of a prospect"""
    try:
        with sqlite3.connect('sales_automation.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get all relevant information in one query
            cursor.execute("""
                SELECT 
                    c.email,
                    c.current_stage,
                    c.updated_at,
                    c.created_at,
                    e.subject,
                    e.sent_at,
                    e.responded,
                    e.responded_at
                FROM contacts c
                LEFT JOIN emails e ON c.email = e.to_email
                WHERE c.email = ?
                ORDER BY e.sent_at DESC
                LIMIT 1
            """, (email,))
            
            result = cursor.fetchone()
            
            if not result:
                return {"error": "Prospect not found"}
                
            return {
                "email": result['email'],
                "stage": result['current_stage'],
                "last_updated": result['updated_at'],
                "first_contact": result['created_at'],
                "latest_email": {
                    "subject": result['subject'],
                    "sent_at": result['sent_at'],
                    "responded": bool(result['responded']),
                    "responded_at": result['responded_at']
                }
            }
            
    except Exception as e:
        return {"error": str(e)}

def main():
    parser = argparse.ArgumentParser(description='Quick prospect status checker')
    parser.add_argument('email', help='Prospect email to check')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    args = parser.parse_args()
    
    status = get_prospect_status(args.email)
    
    if args.json:
        print(json.dumps(status, indent=2))
        return
        
    if "error" in status:
        print(f"Error: {status['error']}")
        return
        
    print("\n=== Prospect Status ===")
    print(f"Email: {status['email']}")
    print(f"Current Stage: {status['stage']}")
    print(f"First Contact: {status['first_contact']}")
    print(f"Last Updated: {status['last_updated']}")
    print("\nLatest Email:")
    print(f"  Subject: {status['latest_email']['subject']}")
    print(f"  Sent: {status['latest_email']['sent_at']}")
    print(f"  Responded: {'Yes' if status['latest_email']['responded'] else 'No'}")
    if status['latest_email']['responded']:
        print(f"  Response received: {status['latest_email']['responded_at']}")

if __name__ == "__main__":
    main()
