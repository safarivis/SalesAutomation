from email_sender import EmailSender
from content_generator import ContentGenerator

# Initialize generators
generator = ContentGenerator()
sender = EmailSender()

# Contact details for test
test_contact = {
    "name": "Dr. Smith",
    "practice_name": "Family Health Practice",
    "specialty": "General Practice"
}

# Custom HTML template
email_template = """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #2c5282;">Transform Your Medical Practice with AI-Powered Solutions</h2>
    
    <p>Dear Dr. {name},</p>
    
    <p>Is your practice experiencing:</p>
    <ul style="list-style-type: none; padding-left: 20px;">
        Overwhelmed reception staff?<br>
        After-hours patient queries?<br>
        Missed appointments?<br>
        Need for a modern online presence?
    </ul>

    <p>We help medical practices like yours overcome these challenges with our <strong>Modern Medical Practice Package</strong>:</p>
    
    <div style="background: #f7fafc; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <strong>1. Professional Website</strong>
        <ul>
            Online appointment booking<br>
            Mobile-friendly design<br>
            Practice information<br>
            Doctor profiles
        </ul>
    </div>

    <div style="background: #f7fafc; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <strong>2. AI Reception Assistant</strong>
        <ul>
            24/7 patient support<br>
            Appointment scheduling<br>
            FAQs & practice information<br>
            Insurance queries
        </ul>
    </div>

    <div style="background: #f7fafc; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <strong>3. Patient Communication Hub</strong>
        <ul>
            Appointment reminders<br>
            Follow-up notifications<br>
            Health tips newsletters<br>
            Patient feedback system
        </ul>
    </div>

    <p><strong>Simple Pricing:</strong></p>
    <ul style="list-style-type: none; padding-left: 20px;">
        One-time setup fee<br>
        Monthly subscription<br>
        No long-term contract
    </ul>

    <p style="text-align: center;">
        <a href="https://calendly.com/your-link" style="background-color: #2c5282; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">See 5-Minute Demo</a>
    </p>

    <p>Best regards,<br>
    Louis du Plessis<br>
    <span style="color: #666;">
    Founder & Healthcare Solutions Architect<br>
    Strijder Online<br>
    <a href="https://strijder.online" style="color: #0066cc; text-decoration: none;">strijder.online</a>
    </span></p>

    <p style="font-size: 0.9em; color: #666; border-top: 1px solid #eee; margin-top: 20px; padding-top: 20px;">
    P.S. Our clients report a 60% reduction in administrative workload and 40% fewer missed appointments.
    </p>
</body>
</html>
"""

# Send email
success = sender.send_email(
    to_email="louisrdup@gmail.com",
    subject="Modernize Your Medical Practice with AI Support",
    content=email_template.format(**test_contact)
)

if success:
    print("Email sent successfully!")
    sender.schedule_follow_ups("louisrdup@gmail.com")
else:
    print("Failed to send email")
