from email_sender import EmailSender
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Override email settings to use Gmail
os.environ['EMAIL_USER'] = os.getenv('GMAIL_USER')
os.environ['EMAIL_PASSWORD'] = os.getenv('GMAIL_APP_PASSWORD')
os.environ['SMTP_SERVER'] = 'smtp.gmail.com'
os.environ['SMTP_PORT'] = '587'

# Read the email template
with open('email_templates/initial_email.html', 'r') as f:
    template = f.read()

# Test contact details
contact = {
    'name': 'Dr. Louis du Plessis',
    'email': 'louisrdup@gmail.com',
    'practice_name': 'Du Plessis Family Practice'
}

# Format the template with contact details
content = template.format(**contact)

# Send the email
sender = EmailSender()
sender.send_email(
    to_email=contact['email'],
    subject='Transform Your Practice with AI: 5-Minute Demo',
    content=content
)

print(f'Sent initial email to {contact["email"]}')
