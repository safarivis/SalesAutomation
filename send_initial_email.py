import sqlite3
from datetime import datetime

email_content = '''Subject: AI Solutions for Software Business Growth

Dear Louis,

I hope this email finds you well. I came across your software company and was particularly impressed by your role as an Owner in the industry. I wanted to reach out because we've been helping software companies leverage AI to accelerate their growth and streamline operations.

As a fellow technology professional, I understand the unique challenges of scaling a software business while maintaining quality and innovation. Our AI solutions have helped companies like yours:

1. Automate customer support and engagement
2. Optimize development workflows
3. Enhance product features with AI capabilities

I'd love to learn more about your specific goals and challenges, and explore how AI could help accelerate your business growth.

Would you be open to a brief call this week to discuss your needs?

Best regards,
Sales Team'''

conn = sqlite3.connect('test_sales.db')
cursor = conn.cursor()

# Log the interaction
cursor.execute('INSERT INTO interactions (contact_email, type, content, timestamp) VALUES (?, ?, ?, ?)', 
              ('louisrdup@gmail.com', 'email', email_content, datetime.now().isoformat()))

# Log the email
cursor.execute('INSERT INTO email_log (from_email, to_email, subject, content, timestamp, status) VALUES (?, ?, ?, ?, ?, ?)',
              ('system@example.com', 'louisrdup@gmail.com', 'AI Solutions for Software Business Growth', 
               email_content, datetime.now().isoformat(), 'pending'))

conn.commit()
conn.close()

print("Initial email created and logged successfully")
