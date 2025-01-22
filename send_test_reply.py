import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

# Email configuration
smtp_server = "smtp.gmail.com"
port = 587
sender_email = os.getenv('GMAIL_USER')
password = os.getenv('GMAIL_APP_PASSWORD')

# Create message
message = MIMEMultipart()
message["From"] = "test@example.com"
message["To"] = sender_email
message["Subject"] = "Re: Your sales outreach"
message["In-Reply-To"] = "<test123@mail.gmail.com>"  # This makes it look like a reply

# Add body
body = """
Hi there,

Yes, I'm interested in learning more about your product. Could we schedule a demo?

Best regards,
Test User
"""
message.attach(MIMEText(body, "plain"))

# Send email
try:
    server = smtplib.SMTP(smtp_server, port)
    server.starttls()
    server.login(sender_email, password)
    server.send_message(message)
    print("Test reply sent successfully!")
except Exception as e:
    print(f"Error sending test reply: {e}")
finally:
    server.quit()
