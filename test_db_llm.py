#!/usr/bin/env python3
"""
Test script for database and LLM functionality using Gemini
"""

import os
import json
import sqlite3
import google.generativeai as genai
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional
import logging
from logging.handlers import RotatingFileHandler

class TestAgent:
    def __init__(self, config_path: str = "config.json"):
        """Initialize test agent with configuration"""
        self.config = self._load_config(config_path)
        self._setup_logging()
        genai.configure(api_key=self.config["gemini_api_key"])
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.db_conn = self._init_database()
        self.logger.info("TestAgent initialized successfully")

    def _setup_logging(self):
        """Setup logging configuration"""
        self.logger = logging.getLogger('SalesAgent')
        self.logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # File handler with rotation
        file_handler = RotatingFileHandler(
            'logs/sales_agent.log',
            maxBytes=1024*1024,  # 1MB
            backupCount=5
        )
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatters and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add the handlers to the logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(config_path) as f:
                return json.load(f)
        except FileNotFoundError:
            raise Exception(f"Configuration file not found at {config_path}")

    def _init_database(self) -> sqlite3.Connection:
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.config["database_path"])
        cursor = conn.cursor()
        
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS contacts (
                email TEXT PRIMARY KEY,
                name TEXT,
                industry TEXT,
                last_contacted TEXT,
                created_at TEXT
            );
            
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_email TEXT,
                type TEXT,
                content TEXT,
                timestamp TEXT,
                FOREIGN KEY (contact_email) REFERENCES contacts(email)
            );
            
            CREATE TABLE IF NOT EXISTS email_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_email TEXT,
                to_email TEXT,
                cc_email TEXT,
                subject TEXT,
                content TEXT,
                timestamp TEXT,
                status TEXT
            );
        """)
        conn.commit()
        self.logger.info("Database initialized successfully")
        return conn

    def add_contact(self, email: str, name: str, industry: str) -> bool:
        """Add a new contact to the database"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                INSERT INTO contacts (email, name, industry, created_at)
                VALUES (?, ?, ?, ?)
            """, (email, name, industry, datetime.now().isoformat()))
            self.db_conn.commit()
            self.logger.info(f"Added new contact: {email}")
            return True
        except sqlite3.IntegrityError:
            self.logger.warning(f"Contact {email} already exists")
            return False
        except Exception as e:
            self.logger.error(f"Error adding contact: {str(e)}")
            return False

    def get_contact(self, email: str) -> Optional[Dict]:
        """Retrieve contact information"""
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT * FROM contacts WHERE email = ?", (email,))
        row = cursor.fetchone()
        if row:
            self.logger.debug(f"Retrieved contact info for {email}")
            return {
                "email": row[0],
                "name": row[1],
                "industry": row[2],
                "last_contacted": row[3],
                "created_at": row[4]
            }
        self.logger.warning(f"Contact not found: {email}")
        return None

    def log_interaction(self, email: str, interaction_type: str, content: str) -> bool:
        """Log an interaction with a contact"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                INSERT INTO interactions (contact_email, type, content, timestamp)
                VALUES (?, ?, ?, ?)
            """, (email, interaction_type, content, datetime.now().isoformat()))
            self.db_conn.commit()
            self.logger.info(f"Logged {interaction_type} interaction for {email}")
            return True
        except Exception as e:
            self.logger.error(f"Error logging interaction: {str(e)}")
            return False

    def log_email(self, from_email: str, to_email: str, subject: str, content: str, 
                 cc_email: str = None, status: str = "sent") -> bool:
        """Log email details"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                INSERT INTO email_log (from_email, to_email, cc_email, subject, content, timestamp, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (from_email, to_email, cc_email, subject, content, 
                 datetime.now().isoformat(), status))
            self.db_conn.commit()
            self.logger.info(f"Logged email to {to_email}")
            return True
        except Exception as e:
            self.logger.error(f"Error logging email: {str(e)}")
            return False

    def get_interactions(self, email: str) -> List[Dict]:
        """Get all interactions for a contact"""
        cursor = self.db_conn.cursor()
        cursor.execute("""
            SELECT type, content, timestamp 
            FROM interactions 
            WHERE contact_email = ? 
            ORDER BY timestamp DESC
        """, (email,))
        interactions = [{"type": row[0], "content": row[1], "timestamp": row[2]} 
                       for row in cursor.fetchall()]
        self.logger.debug(f"Retrieved {len(interactions)} interactions for {email}")
        return interactions

    async def generate_chat_response(self, contact_email: str, user_message: str) -> str:
        """Generate a response using Gemini based on contact history"""
        contact = self.get_contact(contact_email)
        if not contact:
            self.logger.warning(f"Contact not found for response generation: {contact_email}")
            return "Contact not found"
            
        interactions = self.get_interactions(contact_email)
        
        context = f"""
        Contact Information:
        - Name: {contact['name']}
        - Industry: {contact['industry']}
        - Email: {contact['email']}
        
        Previous Interactions:
        {self._format_interactions(interactions)}
        
        Current Message: {user_message}
        
        Instructions: Generate a personalized sales response based on the contact's history and industry. 
        Be empathetic and follow Seth Godin's philosophy of providing value and being genuine.
        """
        
        try:
            self.logger.info(f"Generating response for {contact_email}")
            response = await self.model.generate_content_async(context)
            return response.text
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            self.logger.error(error_msg)
            return error_msg

    def _format_interactions(self, interactions: List[Dict]) -> str:
        """Format interactions for Gemini context"""
        if not interactions:
            return "No previous interactions"
            
        formatted = []
        for interaction in interactions:
            formatted.append(f"[{interaction['timestamp']}] {interaction['type']}: {interaction['content']}")
        return "\n".join(formatted)

    def __del__(self):
        """Cleanup database connection"""
        if hasattr(self, 'db_conn'):
            self.db_conn.close()
            self.logger.info("Database connection closed")

async def main():
    """Main test function"""
    agent = TestAgent()
    
    # Test database operations
    print("Testing database operations...")
    
    # Add a test contact
    test_email = "test@example.com"
    success = agent.add_contact(test_email, "Test User", "Technology")
    print(f"Added contact: {success}")
    
    # Get contact info
    contact = agent.get_contact(test_email)
    print(f"Retrieved contact: {contact}")
    
    # Log some interactions
    agent.log_interaction(test_email, "email", "Initial contact email about AI solutions")
    agent.log_interaction(test_email, "response", "Interested in learning more about your AI consulting services")
    
    # Get interactions
    interactions = agent.get_interactions(test_email)
    print(f"Retrieved interactions: {interactions}")
    
    # Test Gemini integration
    test_message = "I'm interested in your AI consulting services. Can you tell me more about your experience in the technology sector?"
    response = await agent.generate_chat_response(test_email, test_message)
    print(f"\nGemini Response:\n{response}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
