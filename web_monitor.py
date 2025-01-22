#!/usr/bin/env python3
"""
Web-based monitoring dashboard for Sales Automation System
"""

from flask import Flask, render_template_string, jsonify, redirect, request
import sqlite3
import json
from datetime import datetime
import os

app = Flask(__name__)

# HTML template for the dashboard
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Sales Automation Monitor</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .refresh-btn { margin: 10px; }
        .card { margin-bottom: 20px; }
        pre { white-space: pre-wrap; }
    </style>
</head>
<body>
    <div class="container-fluid">
        <h1 class="mt-4">Sales Automation Monitor</h1>
        <button class="btn btn-primary refresh-btn" onclick="refreshData()">Refresh Data</button>
        <button class="btn btn-success refresh-btn" onclick="exportData()">Export Report</button>
        
        <div class="row">
            <!-- Contacts -->
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h3>Contacts</h3>
                    </div>
                    <div class="card-body">
                        <div id="contacts-table"></div>
                    </div>
                </div>
            </div>
            
            <!-- Interactions -->
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h3>Recent Interactions</h3>
                    </div>
                    <div class="card-body">
                        <div id="interactions-table"></div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Email Log -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h3>Email Log</h3>
                    </div>
                    <div class="card-body">
                        <div id="email-log-table"></div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Scheduled Emails -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h3>Scheduled Follow-ups</h3>
                    </div>
                    <div class="card-body">
                        <div id="scheduled-emails-table"></div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- System Log -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h3>System Log</h3>
                    </div>
                    <div class="card-body">
                        <pre id="system-log"></pre>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function refreshData() {
            // Refresh contacts
            $.get('/api/contacts', function(data) {
                let html = '<table class="table table-striped">';
                html += '<thead><tr><th>Email</th><th>Name</th><th>Industry</th><th>Last Contacted</th></tr></thead><tbody>';
                data.forEach(function(contact) {
                    html += `<tr><td>${contact.email}</td><td>${contact.name}</td><td>${contact.industry}</td><td>${contact.last_contacted || 'Never'}</td></tr>`;
                });
                html += '</tbody></table>';
                $('#contacts-table').html(html);
            });
            
            // Refresh interactions
            $.get('/api/interactions', function(data) {
                let html = '<table class="table table-striped">';
                html += '<thead><tr><th>Time</th><th>Contact</th><th>Type</th><th>Content</th></tr></thead><tbody>';
                data.forEach(function(interaction) {
                    html += `<tr><td>${interaction.timestamp}</td><td>${interaction.email}</td><td>${interaction.type}</td><td>${interaction.content}</td></tr>`;
                });
                html += '</tbody></table>';
                $('#interactions-table').html(html);
            });
            
            // Refresh email log
            $.get('/api/email-log', function(data) {
                let html = '<table class="table table-striped">';
                html += '<thead><tr><th>Time</th><th>From</th><th>To</th><th>CC</th><th>Subject</th><th>Status</th><th>Opens</th><th>Clicks</th></tr></thead><tbody>';
                data.forEach(function(email) {
                    html += `<tr>
                        <td>${email.timestamp}</td>
                        <td>${email.from_email}</td>
                        <td>${email.to_email}</td>
                        <td>${email.cc_email or ''}</td>
                        <td>${email.subject}</td>
                        <td>${email.status}</td>
                        <td>${'✓ ' + email.opened_at if email.opened_at else '✗'}</td>
                        <td>${email.click_count or 0}</td>
                    </tr>`;
                });
                html += '</tbody></table>';
                $('#email-log-table').html(html);
            });
            
            // Refresh scheduled emails
            $.get('/api/scheduled-emails', function(data) {
                let html = '<table class="table table-striped">';
                html += '<thead><tr><th>Contact</th><th>Subject</th><th>Scheduled For</th><th>Status</th><th>Sent At</th></tr></thead><tbody>';
                data.forEach(function(email) {
                    html += `<tr>
                        <td>${email.contact_email}</td>
                        <td>${email.subject}</td>
                        <td>${email.scheduled_date}</td>
                        <td>${email.status}</td>
                        <td>${email.sent_at || '-'}</td>
                    </tr>`;
                });
                html += '</tbody></table>';
                $('#scheduled-emails-table').html(html);
            });
            
            // Refresh system log
            $.get('/api/system-log', function(data) {
                $('#system-log').text(data.log);
            });
        }
        
        function exportData() {
            window.location.href = '/export';
        }
        
        // Refresh data every 60 seconds
        refreshData();
        setInterval(refreshData, 60000);
    </script>
</body>
</html>
"""

class Monitor:
    def __init__(self, config_path: str = "config.json"):
        with open(config_path) as f:
            self.config = json.load(f)
    
    def get_db_connection(self):
        return sqlite3.connect(self.config["database_path"])
    
    def get_contacts(self):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT email, name, industry, last_contacted FROM contacts")
        contacts = [{"email": row[0], "name": row[1], "industry": row[2], "last_contacted": row[3]} 
                   for row in cursor.fetchall()]
        conn.close()
        return contacts
    
    def get_interactions(self, limit=50):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT i.timestamp, c.email, i.type, i.content 
            FROM interactions i
            JOIN contacts c ON i.contact_email = c.email
            ORDER BY i.timestamp DESC
            LIMIT ?
        """, (limit,))
        interactions = [{"timestamp": row[0], "email": row[1], "type": row[2], "content": row[3]} 
                       for row in cursor.fetchall()]
        conn.close()
        return interactions
    
    def get_email_log(self, limit=50):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, from_email, to_email, cc_email, subject, status,
                   tracking_id, opened_at, click_count
            FROM email_log
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        emails = [{"timestamp": row[0], "from_email": row[1], "to_email": row[2],
                  "cc_email": row[3], "subject": row[4], "status": row[5],
                  "tracking_id": row[6], "opened_at": row[7], "click_count": row[8]} 
                 for row in cursor.fetchall()]
        conn.close()
        return emails
    
    def get_scheduled_emails(self):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT contact_email, subject, scheduled_date, status, sent_at
            FROM scheduled_emails
            ORDER BY scheduled_date
        """)
        scheduled = [{"contact_email": row[0], "subject": row[1],
                     "scheduled_date": row[2], "status": row[3],
                     "sent_at": row[4]} 
                    for row in cursor.fetchall()]
        conn.close()
        return scheduled
    
    def get_system_log(self, lines=100):
        try:
            with open('logs/sales_agent.log', 'r') as f:
                return ''.join(f.readlines()[-lines:])
        except FileNotFoundError:
            return "No log file found"
    
    def export_report(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sales_report_{timestamp}.html"
        
        contacts = self.get_contacts()
        interactions = self.get_interactions(100)
        emails = self.get_email_log(100)
        
        report = f"""
        <html>
        <head>
            <title>Sales Automation Report - {timestamp}</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container">
                <h1>Sales Automation Report</h1>
                <p>Generated: {timestamp}</p>
                
                <h2>Contacts</h2>
                <table class="table table-striped">
                    <thead><tr><th>Email</th><th>Name</th><th>Industry</th><th>Last Contacted</th></tr></thead>
                    <tbody>
                        {"".join(f"<tr><td>{c['email']}</td><td>{c['name']}</td><td>{c['industry']}</td><td>{c['last_contacted'] or 'Never'}</td></tr>" for c in contacts)}
                    </tbody>
                </table>
                
                <h2>Recent Interactions</h2>
                <table class="table table-striped">
                    <thead><tr><th>Time</th><th>Contact</th><th>Type</th><th>Content</th></tr></thead>
                    <tbody>
                        {"".join(f"<tr><td>{i['timestamp']}</td><td>{i['email']}</td><td>{i['type']}</td><td>{i['content']}</td></tr>" for i in interactions)}
                    </tbody>
                </table>
                
                <h2>Email Log</h2>
                <table class="table table-striped">
                    <thead><tr><th>Time</th><th>From</th><th>To</th><th>CC</th><th>Subject</th><th>Status</th><th>Opens</th><th>Clicks</th></tr></thead>
                    <tbody>
                        {"".join(f"<tr><td>{e['timestamp']}</td><td>{e['from_email']}</td><td>{e['to_email']}</td><td>{e['cc_email'] or ''}</td><td>{e['subject']}</td><td>{e['status']}</td><td>{'✓ ' + e['opened_at'] if e['opened_at'] else '✗'}</td><td>{e['click_count'] or 0}</td></tr>" for e in emails)}
                    </tbody>
                </table>
            </div>
        </body>
        </html>
        """
        
        with open(filename, 'w') as f:
            f.write(report)
        
        return filename

monitor = Monitor()

@app.route('/')
def dashboard():
    return render_template_string(DASHBOARD_TEMPLATE)

@app.route('/api/contacts')
def api_contacts():
    return jsonify(monitor.get_contacts())

@app.route('/api/interactions')
def api_interactions():
    return jsonify(monitor.get_interactions())

@app.route('/api/email-log')
def api_email_log():
    return jsonify(monitor.get_email_log())

@app.route('/api/scheduled-emails')
def api_scheduled_emails():
    return jsonify(monitor.get_scheduled_emails())

@app.route('/api/system-log')
def api_system_log():
    return jsonify({"log": monitor.get_system_log()})

@app.route('/track/open/<tracking_id>')
def track_open(tracking_id):
    conn = monitor.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE email_log 
        SET opened_at = ? 
        WHERE tracking_id = ? AND opened_at IS NULL
    """, (datetime.now().isoformat(), tracking_id))
    conn.commit()
    conn.close()
    return '', 204

@app.route('/track/click/<tracking_id>')
def track_click(tracking_id):
    url = request.args.get('url')
    if not url:
        return 'Missing URL', 400
    
    conn = monitor.get_db_connection()
    cursor = conn.cursor()
    
    # Log the click
    cursor.execute("""
        INSERT INTO email_clicks (tracking_id, url, clicked_at)
        VALUES (?, ?, ?)
    """, (tracking_id, url, datetime.now().isoformat()))
    
    # Update click count
    cursor.execute("""
        UPDATE email_log 
        SET click_count = click_count + 1
        WHERE tracking_id = ?
    """, (tracking_id,))
    
    conn.commit()
    conn.close()
    
    return redirect(url)

@app.route('/export')
def export():
    filename = monitor.export_report()
    return f"""
    <html>
        <body>
            <p>Report generated: <a href="{filename}">{filename}</a></p>
            <script>
                window.location.href = "{filename}";
            </script>
        </body>
    </html>
    """

if __name__ == "__main__":
    app.run(debug=True, port=5000)
