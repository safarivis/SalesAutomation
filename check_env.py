from dotenv import load_dotenv
import os

load_dotenv()

print(f"GMAIL_USER: {os.getenv('GMAIL_USER')}")
print(f"GMAIL_APP_PASSWORD length: {len(os.getenv('GMAIL_APP_PASSWORD') or '')}")
