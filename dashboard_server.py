#!/usr/bin/env python3
"""
Dashboard Server - Serves the sales automation dashboard
"""

from flask import Flask, render_template, send_from_directory
import os
from quick_api import api
from quick_monitor import QuickMonitor
import threading

app = Flask(__name__)

# Register API blueprint
app.register_blueprint(api, url_prefix='/api')

# Configure JWT secret
app.config['SECRET_KEY'] = os.getenv('JWT_SECRET', 'your-secret-key')

@app.route('/')
def dashboard():
    """Serve the main dashboard"""
    return render_template('dashboard.html')

@app.route('/static/<path:path>')
def send_static(path):
    """Serve static files"""
    return send_from_directory('static', path)

def start_monitor():
    """Start the email monitor in a separate thread"""
    monitor = QuickMonitor()
    monitor_thread = threading.Thread(target=monitor.run, daemon=True)
    monitor_thread.start()

if __name__ == '__main__':
    # Start the email monitor
    start_monitor()
    
    # Start the dashboard server
    app.run(port=5000, debug=True)
