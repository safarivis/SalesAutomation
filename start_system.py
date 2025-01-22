#!/usr/bin/env python3
"""
Main entry point for the Sales Automation System
"""

import subprocess
import signal
import sys
import os
from dotenv import load_dotenv

def main():
    load_dotenv()
    
    # Start email monitor
    email_monitor = subprocess.Popen(
        [os.path.join("venv", "bin", "python"), "email_monitor.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Start web dashboard
    dashboard = subprocess.Popen(
        [os.path.join("venv", "bin", "flask"), "--app", "web_monitor", "run", "--host", "0.0.0.0", "--port", "5000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    def signal_handler(sig, frame):
        print("\nShutting down gracefully...")
        email_monitor.terminate()
        dashboard.terminate()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        email_monitor.wait()
        dashboard.wait()
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        email_monitor.terminate()
        dashboard.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()
