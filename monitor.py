#!/usr/bin/env python3
"""
Monitoring dashboard for Sales Automation System
"""

import sqlite3
import tkinter as tk
from tkinter import ttk
import json
from datetime import datetime
import webbrowser
from typing import Dict, List, Optional
import os

class MonitorDashboard:
    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.root = tk.Tk()
        self.root.title("Sales Automation Monitor")
        self.root.geometry("1200x800")
        
        # Create main container
        self.main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Left panel for contacts
        self.contacts_frame = ttk.LabelFrame(self.main_container, text="Contacts")
        self.main_container.add(self.contacts_frame)
        
        # Right panel for interactions
        self.interactions_frame = ttk.LabelFrame(self.main_container, text="Interactions")
        self.main_container.add(self.interactions_frame)
        
        # Add notifications frame
        self.notifications_frame = ttk.LabelFrame(self.root, text="Notifications")
        self.notifications_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Initialize components
        self._setup_contacts_panel()
        self._setup_interactions_view()
        self._setup_notifications_panel()
        
        # Refresh button
        ttk.Button(self.root, text="Refresh", command=self.refresh_data).pack(pady=5)
        
        # Export button
        ttk.Button(self.root, text="Export to HTML", command=self.export_to_html).pack(pady=5)
        
        # Auto-refresh every 60 seconds
        self.root.after(60000, self.refresh_data)
        
        # Start monitoring for responses
        self.monitor_responses()

    def _load_config(self, config_path: str) -> Dict:
        with open(config_path) as f:
            return json.load(f)

    def _setup_contacts_panel(self):
        """Setup the contacts panel with stages"""
        # Create treeview
        columns = ('Email', 'Stage', 'Last Updated', 'Interactions')
        self.contacts_tree = ttk.Treeview(self.contacts_frame, columns=columns, show='headings')
        
        # Add headings
        for col in columns:
            self.contacts_tree.heading(col, text=col)
            self.contacts_tree.column(col, width=150)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.contacts_frame, orient=tk.VERTICAL, command=self.contacts_tree.yview)
        self.contacts_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.contacts_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click to show history
        self.contacts_tree.bind('<Double-1>', self._show_contact_history)

    def _show_contact_history(self, event):
        """Show contact's stage history"""
        item = self.contacts_tree.selection()[0]
        email = self.contacts_tree.item(item, 'values')[0]
        
        # Create popup window
        popup = tk.Toplevel(self.root)
        popup.title(f"History for {email}")
        popup.geometry("600x400")
        
        # Create treeview for history
        columns = ('Timestamp', 'Changed From', 'Changed To')
        history_tree = ttk.Treeview(popup, columns=columns, show='headings')
        
        for col in columns:
            history_tree.heading(col, text=col)
            history_tree.column(col, width=150)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(popup, orient=tk.VERTICAL, command=history_tree.yview)
        history_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Fetch and display history
        conn = sqlite3.connect(self.config.get("database", "sales.db"))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT s.changed_at, s.changed_from, s.changed_to
            FROM contacts c
            JOIN stages s ON c.id = s.contact_id
            WHERE c.email = ?
            ORDER BY s.changed_at DESC
        ''', (email,))
        
        for row in cursor.fetchall():
            history_tree.insert('', tk.END, values=row)
        
        conn.close()

    def _setup_interactions_view(self):
        # Create Treeview for interactions
        columns = ("Timestamp", "Type", "Content")
        self.interactions_tree = ttk.Treeview(self.interactions_frame, columns=columns, show="headings")
        
        # Set column headings
        for col in columns:
            self.interactions_tree.heading(col, text=col)
        self.interactions_tree.column("Timestamp", width=150)
        self.interactions_tree.column("Type", width=100)
        self.interactions_tree.column("Content", width=400)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.interactions_frame, orient=tk.VERTICAL, command=self.interactions_tree.yview)
        self.interactions_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.interactions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _setup_notifications_panel(self):
        """Setup the notifications panel"""
        self.notifications_text = tk.Text(self.notifications_frame, height=4)
        self.notifications_text.pack(fill=tk.X, padx=5, pady=5)
        self.notifications_text.config(state=tk.DISABLED)
    
    def add_notification(self, message: str):
        """Add a notification message"""
        self.notifications_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.notifications_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.notifications_text.see(tk.END)
        self.notifications_text.config(state=tk.DISABLED)
    
    def monitor_responses(self):
        """Check for new responses periodically"""
        conn = sqlite3.connect(self.config.get("database", "sales.db"))
        cursor = conn.cursor()
        
        # Check for new responses
        cursor.execute("""
            SELECT recipient_email, subject, responded_time 
            FROM email_tracking 
            WHERE responded = TRUE 
            AND responded_time > datetime('now', '-1 minute')
        """)
        
        new_responses = cursor.fetchall()
        for email, subject, time in new_responses:
            self.add_notification(f"New response from {email} to '{subject}'")
        
        conn.close()
        
        # Check again in 60 seconds
        self.root.after(60000, self.monitor_responses)

    def refresh_data(self):
        """Refresh all data in the dashboard"""
        conn = sqlite3.connect(self.config.get("database", "sales.db"))
        cursor = conn.cursor()
        
        # Clear existing items
        for item in self.contacts_tree.get_children():
            self.contacts_tree.delete(item)
        
        # Fetch and display contacts with their current stages
        cursor.execute('''
            SELECT 
                c.email,
                c.current_stage,
                c.stage_updated_at,
                COUNT(e.id) as interaction_count
            FROM contacts c
            LEFT JOIN email_tracking e ON c.id = e.contact_id
            GROUP BY c.id
            ORDER BY c.stage_updated_at DESC
        ''')
        
        for row in cursor.fetchall():
            self.contacts_tree.insert('', tk.END, values=row)
        
        conn.close()
        self._refresh_interactions()

    def _refresh_interactions(self, email: str = None):
        """Refresh interactions list"""
        # Clear existing items
        for item in self.interactions_tree.get_children():
            self.interactions_tree.delete(item)
            
        if email:
            # Get interactions for specific contact
            conn = sqlite3.connect(self.config.get("database", "sales.db"))
            cursor = conn.cursor()
            cursor.execute("""
                SELECT timestamp, type, content 
                FROM interactions 
                WHERE contact_email = ?
                ORDER BY timestamp DESC
            """, (email,))
            
            for row in cursor.fetchall():
                self.interactions_tree.insert("", tk.END, values=row)
                
            conn.close()

    def on_contact_select(self, event):
        """Handle contact selection"""
        selection = self.contacts_tree.selection()
        if selection:
            item = self.contacts_tree.item(selection[0])
            email = item["values"][0]
            self._refresh_interactions(email)

    def export_to_html(self):
        """Export current view to HTML"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sales_monitor_{timestamp}.html"
        
        html_content = """
        <html>
        <head>
            <title>Sales Automation Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                h2 { color: #333; }
            </style>
        </head>
        <body>
        """
        
        # Add contacts table
        html_content += "<h2>Contacts</h2>"
        html_content += "<table><tr><th>Email</th><th>Stage</th><th>Last Updated</th><th>Interactions</th></tr>"
        
        conn = sqlite3.connect(self.config.get("database", "sales.db"))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                c.email,
                c.current_stage,
                c.stage_updated_at,
                COUNT(e.id) as interaction_count
            FROM contacts c
            LEFT JOIN email_tracking e ON c.id = e.contact_id
            GROUP BY c.id
            ORDER BY c.stage_updated_at DESC
        ''')
        
        for row in cursor.fetchall():
            html_content += f"<tr><td>{'</td><td>'.join(str(x) for x in row)}</td></tr>"
        
        html_content += "</table>"
        
        # Add interactions table
        html_content += "<h2>Recent Interactions</h2>"
        html_content += "<table><tr><th>Timestamp</th><th>Contact</th><th>Type</th><th>Content</th></tr>"
        
        cursor.execute("""
            SELECT i.timestamp, c.email, i.type, i.content 
            FROM interactions i
            JOIN contacts c ON i.contact_email = c.email
            ORDER BY i.timestamp DESC
            LIMIT 100
        """)
        
        for row in cursor.fetchall():
            html_content += f"<tr><td>{'</td><td>'.join(str(x) for x in row)}</td></tr>"
        
        html_content += "</table></body></html>"
        
        conn.close()
        
        with open(filename, 'w') as f:
            f.write(html_content)
            
        # Open in browser
        webbrowser.open(filename)

    def run(self):
        """Start the dashboard"""
        self.refresh_data()
        self.root.mainloop()

def main():
    dashboard = MonitorDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()
