import google.generativeai as genai
import json
import os
from typing import Dict
from dotenv import load_dotenv

class ContentGenerator:
    def __init__(self, config_path: str = "config.json"):
        load_dotenv()
        with open(config_path) as f:
            self.config = json.load(f)
        
        genai.configure(api_key=self.config.get('gemini_api_key') or os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-pro')
    
    def generate_initial_email(self, contact: Dict) -> str:
        """Generate initial email content for medical practices"""
        prompt = f"""
        Create a concise, direct cold email for medical practitioners. The email should:
        1. Address their biggest pain point immediately
        2. Present a clear, complete solution
        3. Show immediate ROI
        4. Make a simple offer

        Contact Details:
        - Name: {contact['name']}
        - Practice: {contact['practice_name']}
        - Specialty: {contact['specialty']}

        Our Complete Package:
        "Modern Medical Practice Solution"
        
        1. Professional Website
           - Online appointment booking
           - Mobile-friendly design
           - Practice information
           - Doctor profiles
        
        2. AI Reception Assistant
           - 24/7 patient support
           - Appointment scheduling
           - FAQs & practice information
           - Insurance queries
        
        3. Patient Communication Hub
           - Appointment reminders
           - Follow-up notifications
           - Health tips newsletters
           - Patient feedback system

        Key Benefits:
        1. Reduce reception workload by 60%
        2. Eliminate after-hours queries
        3. Cut missed appointments by 40%
        4. Modern, professional online presence
        5. Better patient satisfaction

        Pricing:
        - One-time setup
        - Simple monthly subscription
        - No long-term contract required

        Call to Action:
        "See a 5-minute demo of your practice's AI assistant"
        
        Format the email in HTML with this specific styling:
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        [Content here]
        <p>Best regards,<br>
        Louis du Plessis<br>
        <span style="color: #666;">
        Founder & Healthcare Solutions Architect<br>
        Strijder Online<br>
        <a href="https://strijder.online" style="color: #0066cc; text-decoration: none;">strijder.online</a>
        </span></p>
        </body>
        </html>

        Guidelines:
        - Maximum 150 words
        - Focus on their biggest pain point first
        - Use bullet points for quick scanning
        - Include one clear call to action
        - Add a P.S. with a compelling stat
        """
        
        response = self.model.generate_content(prompt)
        return response.text
    
    def generate_follow_up(self, contact: Dict, sequence_number: int) -> str:
        """Generate follow-up email content"""
        prompt = f"""
        Create a follow-up email (#{sequence_number}) that builds on Seth Godin's tribe-building principles. The email should:
        1. Add value with each touch point
        2. Share insights or resources relevant to their challenges
        3. Continue building the relationship without being pushy
        4. Reinforce the movement and community aspect

        Contact Details:
        - Name: {contact['name']}
        - Industry: {contact['industry']}
        - Role: {contact['job_title']}

        Follow-up Context:
        - This is follow-up #{sequence_number}
        - Previous emails focused on AI solutions for software companies
        - We want to share valuable insights even if they don't respond

        Guidelines:
        - Start with a fresh angle or insight
        - Share a quick win or actionable tip
        - Keep building trust and authority
        - Make it easy to respond
        - Keep it shorter than the initial email
        - Include a P.S. with additional value

        Format the email in HTML with appropriate styling.
        """
        
        response = self.model.generate_content(prompt)
        return response.text

if __name__ == "__main__":
    # Test the content generator
    generator = ContentGenerator()
    test_contact = {
        "name": "Louis du Plessis",
        "practice_name": "Test Practice",
        "specialty": "General Practice"
    }
    
    print("Generating initial email...")
    initial_email = generator.generate_initial_email(test_contact)
    print("\nInitial Email Content:")
    print(initial_email)
    
    print("\nGenerating follow-up email...")
    follow_up = generator.generate_follow_up({"name": "Louis du Plessis", "industry": "Software", "job_title": "Owner"}, 1)
    print("\nFollow-up Email Content:")
    print(follow_up)
