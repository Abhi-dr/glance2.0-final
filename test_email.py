import os
import sys
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get email settings from environment variables
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = os.environ.get('EMAIL_PORT')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS')

def test_email_settings():
    """Test the email settings and print them"""
    print("Email Settings:")
    print(f"EMAIL_HOST: {EMAIL_HOST}")
    print(f"EMAIL_PORT: {EMAIL_PORT}")
    print(f"EMAIL_HOST_USER: {EMAIL_HOST_USER}")
    print(f"EMAIL_HOST_PASSWORD: {'*' * 8 if EMAIL_HOST_PASSWORD else 'Not set'}")
    print(f"EMAIL_USE_TLS: {EMAIL_USE_TLS}")

def test_smtp_connection():
    """Test the SMTP connection"""
    print("\nTesting SMTP Connection...")
    try:
        if EMAIL_USE_TLS:
            smtp = smtplib.SMTP(EMAIL_HOST, int(EMAIL_PORT))
            smtp.ehlo()
            smtp.starttls()
        else:
            smtp = smtplib.SMTP(EMAIL_HOST, int(EMAIL_PORT))
        
        smtp.ehlo()
        smtp.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        print("SMTP Connection: SUCCESS")
        smtp.quit()
        return True
    except Exception as e:
        print(f"SMTP Connection: FAILED")
        print(f"Error: {str(e)}")
        return False

def send_test_email(to_email):
    """Send a test email"""
    print(f"\nSending test email to {to_email}...")
    
    msg = MIMEText("This is a test email from the GLANCE system.")
    msg['Subject'] = "GLANCE Test Email"
    msg['From'] = f"GLANCE JOB FAIR 2k24 <{EMAIL_HOST_USER}>"
    msg['To'] = to_email
    
    try:
        smtp = smtplib.SMTP(EMAIL_HOST, int(EMAIL_PORT))
        smtp.ehlo()
        if EMAIL_USE_TLS:
            smtp.starttls()
            smtp.ehlo()
        
        smtp.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        smtp.send_message(msg)
        smtp.quit()
        print("Test email sent successfully!")
        return True
    except Exception as e:
        print(f"Failed to send test email!")
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_email_settings()
    
    if test_smtp_connection():
        # If connection test passed, ask for an email address to send a test email
        to_email = input("\nEnter an email address to send a test email: ")
        send_test_email(to_email)
    else:
        print("\nSMTP connection test failed. Please fix the connection issues before sending a test email.") 