#!/usr/bin/env python3
"""
Quick API - RESTful interface for Sales Automation
"""

from flask import Flask, jsonify, request, Blueprint, current_app
import sqlite3
from datetime import datetime
import os
from dotenv import load_dotenv
import jwt
from functools import wraps
import threading
from quick_monitor import QuickMonitor

# Load environment variables
load_dotenv()

# Create Blueprint
api = Blueprint('api', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Temporarily disable token requirement
        return f(*args, **kwargs)
    return decorated

# Database helper
def get_db():
    db = sqlite3.connect('sales_automation.db')
    db.row_factory = sqlite3.Row
    return db

@api.route('/prospects', methods=['GET'])
@token_required
def get_prospects():
    """Get all prospects with optional filters"""
    db = get_db()
    cursor = db.cursor()
    
    prospects = []
    for row in cursor.execute('SELECT * FROM contacts ORDER BY updated_at DESC'):
        prospect = dict(row)
        # Get email stats
        email_stats = cursor.execute('''
            SELECT COUNT(*) as total_emails,
                   SUM(CASE WHEN responded = 1 THEN 1 ELSE 0 END) as responses
            FROM emails WHERE to_email = ?
        ''', (row['email'],)).fetchone()
        prospect['total_emails'] = email_stats['total_emails']
        prospect['response_rate'] = (email_stats['responses'] / email_stats['total_emails'] * 100) if email_stats['total_emails'] > 0 else 0
        prospects.append(prospect)
        
    return jsonify(prospects)

@api.route('/metrics', methods=['GET'])
@token_required
def get_metrics():
    """Get campaign metrics"""
    db = get_db()
    cursor = db.cursor()
    
    # Get total prospects
    total_prospects = cursor.execute('SELECT COUNT(*) as count FROM contacts').fetchone()['count']
    
    # Get response rate
    email_stats = cursor.execute('''
        SELECT COUNT(*) as total_emails,
               SUM(CASE WHEN responded = 1 THEN 1 ELSE 0 END) as responses
        FROM emails
    ''').fetchone()
    response_rate = (email_stats['responses'] / email_stats['total_emails'] * 100) if email_stats['total_emails'] > 0 else 0
    
    # Get demo scheduled count
    demo_scheduled = cursor.execute('''
        SELECT COUNT(*) as count FROM contacts 
        WHERE current_stage = 'demo_scheduled'
    ''').fetchone()['count']
    
    # Get conversion rate (prospects in 'converted' stage)
    converted = cursor.execute('''
        SELECT COUNT(*) as count FROM contacts 
        WHERE current_stage = 'converted'
    ''').fetchone()['count']
    conversion_rate = (converted / total_prospects * 100) if total_prospects > 0 else 0
    
    # Get stage distribution
    stages = cursor.execute('''
        SELECT current_stage, COUNT(*) as count 
        FROM contacts 
        GROUP BY current_stage
    ''').fetchall()
    
    # Get recent activity
    recent_activity = cursor.execute('''
        SELECT 'email' as type, e.sent_at as timestamp, 
               e.from_email, e.to_email, e.subject,
               CASE WHEN e.responded = 1 THEN 'responded' ELSE 'sent' END as action
        FROM emails e
        UNION ALL
        SELECT 'stage' as type, s.changed_at as timestamp,
               s.email, '', '',
               'moved from ' || s.old_stage || ' to ' || s.new_stage as action
        FROM stages s
        ORDER BY timestamp DESC
        LIMIT 10
    ''').fetchall()
    
    metrics = {
        'total_prospects': total_prospects,
        'response_rate': round(response_rate, 1),
        'demo_scheduled': demo_scheduled,
        'conversion_rate': round(conversion_rate, 1),
        'stage_distribution': [dict(row) for row in stages],
        'recent_activity': [dict(row) for row in recent_activity]
    }
        
    return jsonify(metrics)

@api.route('/search', methods=['GET'])
@token_required
def search_prospects():
    """Search prospects by email or stage"""
    query = request.args.get('q', '')
    db = get_db()
    cursor = db.cursor()
    
    results = cursor.execute('''
        SELECT * FROM contacts 
        WHERE email LIKE ? OR current_stage LIKE ?
        ORDER BY updated_at DESC
    ''', (f'%{query}%', f'%{query}%')).fetchall()
    
    return jsonify([dict(row) for row in results])

@api.route('/stage/<email>', methods=['PUT'])
@token_required
def update_stage(email):
    """Update prospect stage"""
    new_stage = request.json.get('stage')
    if not new_stage:
        return jsonify({'error': 'Stage not provided'}), 400
        
    db = get_db()
    cursor = db.cursor()
    
    # Get current stage
    current = cursor.execute('SELECT current_stage FROM contacts WHERE email = ?', 
                           (email,)).fetchone()
    if not current:
        return jsonify({'error': 'Prospect not found'}), 404
        
    # Update contact stage
    cursor.execute('''
        UPDATE contacts 
        SET current_stage = ?, updated_at = datetime('now')
        WHERE email = ?
    ''', (new_stage, email))
    
    # Record stage change
    cursor.execute('''
        INSERT INTO stages (email, old_stage, new_stage)
        VALUES (?, ?, ?)
    ''', (email, current['current_stage'], new_stage))
    
    db.commit()
    return jsonify({'message': 'Stage updated'})

@api.route('/webhook', methods=['POST'])
@token_required
def webhook():
    """Handle webhooks from email service"""
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
        
    db = get_db()
    cursor = db.cursor()
    
    # Update email status
    if data.get('type') == 'email_response':
        cursor.execute('''
            UPDATE emails 
            SET responded = 1, responded_at = datetime('now')
            WHERE message_id = ?
        ''', (data['message_id'],))
        db.commit()
        
    return jsonify({'message': 'Webhook processed'})

def start_monitor():
    """Start the email monitor in a separate thread"""
    monitor = QuickMonitor()
    monitor_thread = threading.Thread(target=monitor.run, daemon=True)
    monitor_thread.start()

if __name__ == '__main__':
    # Create Flask app
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('JWT_SECRET', 'your-secret-key')
    app.register_blueprint(api, url_prefix='/api')
    
    # Start the monitor
    start_monitor()
    
    # Start the API server
    app.run(port=5001)
