import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get email settings from environment variables
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT'))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS') == 'True'

print("Email Settings:")
print(f"EMAIL_HOST: {EMAIL_HOST}")
print(f"EMAIL_PORT: {EMAIL_PORT}")
print(f"EMAIL_HOST_USER: {EMAIL_HOST_USER}")
print(f"EMAIL_HOST_PASSWORD: {'*' * 8 if EMAIL_HOST_PASSWORD else 'Not set'}")
print(f"EMAIL_USE_TLS: {EMAIL_USE_TLS}")

try:
    # Create a connection
    print("\nAttempting to connect to SMTP server...")
    smtp = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
    smtp.ehlo()
    
    if EMAIL_USE_TLS:
        print("Starting TLS...")
        smtp.starttls()
        smtp.ehlo()
    
    print(f"Attempting to log in as {EMAIL_HOST_USER}...")
    smtp.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
    print("Login successful!")
    
    # Close the connection
    smtp.quit()
    print("SMTP connection test successful!")

except Exception as e:
    print(f"Error: {str(e)}")
    print("SMTP connection test failed.") 