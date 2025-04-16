#!/usr/bin/env python3
"""
WhatsApp Automation Script for Bulk Messaging
============================================
This script automates sending WhatsApp messages using WhatsApp Web.
It reads recipient data from a CSV file, sends personalized messages,
and tracks sent messages to avoid duplicates.
"""

import os
import csv
import time
import random
import logging
from datetime import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("whatsapp_automation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WhatsAppAutomation:
    """Class to handle WhatsApp Web automation for sending messages"""
    
    def __init__(self, user_data_dir=None, chrome_driver_path=None):
        """
        Initialize WhatsApp automation
        
        Args:
            user_data_dir (str): Path to Chrome user data directory
            chrome_driver_path (str): Path to Chrome driver executable
        """
        self.user_data_dir = user_data_dir or os.path.join(os.path.expanduser("~"), "whatsapp_automation")
        self.chrome_driver_path = chrome_driver_path
        self.driver = None
        self.sent_log_file = "sent_messages.csv"
        self.sent_numbers = self._load_sent_numbers()
        
    def _load_sent_numbers(self):
        """Load already sent phone numbers from log file"""
        sent_numbers = set()
        if os.path.exists(self.sent_log_file):
            try:
                with open(self.sent_log_file, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader, None)  # Skip header
                    for row in reader:
                        if row and len(row) > 0:
                            sent_numbers.add(row[0])  # First column is phone number
                logger.info(f"Loaded {len(sent_numbers)} previously sent numbers")
            except Exception as e:
                logger.error(f"Error loading sent numbers: {e}")
        return sent_numbers
    
    def _save_sent_number(self, phone, name, status):
        """Save sent number to log file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header_needed = not os.path.exists(self.sent_log_file)
        
        try:
            with open(self.sent_log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if header_needed:
                    writer.writerow(['Phone', 'Name', 'Status', 'Timestamp'])
                writer.writerow([phone, name, status, timestamp])
            
            # Add to in-memory set
            self.sent_numbers.add(phone)
        except Exception as e:
            logger.error(f"Error saving sent number: {e}")
    
    def initialize_driver(self):
        """Initialize Chrome WebDriver with custom options"""
        try:
            options = Options()
            
            # Set up Chrome profile to keep WhatsApp Web session
            options.add_argument(f"user-data-dir={self.user_data_dir}")
            
            # Additional options for better stability
            options.add_argument("--disable-notifications")
            options.add_argument("--disable-infobars")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1366,768")
            
            # Initialize the driver
            if self.chrome_driver_path:
                service = Service(executable_path=self.chrome_driver_path)
                self.driver = webdriver.Chrome(service=service, options=options)
            else:
                self.driver = webdriver.Chrome(options=options)
                
            self.driver.maximize_window()
            logger.info("Chrome WebDriver initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            return False
    
    def login_to_whatsapp(self, timeout=60):
        """
        Navigate to WhatsApp Web and wait for login
        
        Args:
            timeout (int): Maximum time to wait for login in seconds
        
        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            self.driver.get("https://web.whatsapp.com/")
            logger.info("Navigated to WhatsApp Web")
            
            # Wait for WhatsApp to load
            try:
                # Wait for the search box to appear, indicating we're logged in
                search_box = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@title="Search input textbox"]'))
                )
                logger.info("Successfully logged into WhatsApp Web")
                return True
                
            except TimeoutException:
                logger.error(f"Login timed out after {timeout} seconds")
                
                # Check if QR code is present
                try:
                    qr_code = self.driver.find_element(By.XPATH, '//canvas[@aria-label="Scan me!"]')
                    logger.warning("QR code detected. Please scan it using your phone")
                    
                    # Give extra time to scan QR code
                    try:
                        search_box = WebDriverWait(self.driver, 120).until(
                            EC.presence_of_element_located((By.XPATH, '//div[@title="Search input textbox"]'))
                        )
                        logger.info("QR code successfully scanned and logged in")
                        return True
                    except TimeoutException:
                        logger.error("Failed to login even after QR code scan")
                        return False
                        
                except NoSuchElementException:
                    logger.error("QR code not found and not logged in")
                    return False
                    
        except Exception as e:
            logger.error(f"Error during WhatsApp login: {e}")
            return False
    
    def send_message(self, phone, message, name=""):
        """
        Send a WhatsApp message to a specific phone number
        
        Args:
            phone (str): Phone number including country code (e.g., "919876543210")
            message (str): Message to send
            name (str): Name of the recipient for logging
            
        Returns:
            bool: True if successful, False otherwise
        """
        if phone in self.sent_numbers:
            logger.info(f"Skipping {phone} ({name}) - Already sent ⏭️")
            return True
            
        # Format phone number (remove + if present)
        if phone.startswith('+'):
            phone = phone[1:]
            
        try:
            # Direct URL to chat with the phone number
            chat_url = f"https://web.whatsapp.com/send?phone={phone}"
            self.driver.get(chat_url)
            
            # Wait for the chat to load
            try:
                # Wait for message input box
                message_box = WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@title="Type a message"]'))
                )
                
                # Check if "Phone number shared via url is invalid" appears
                try:
                    invalid_notice = self.driver.find_element(By.XPATH, '//*[contains(text(), "Phone number shared via url is invalid")]')
                    logger.error(f"Invalid phone number: {phone} ({name}) ❌")
                    self._save_sent_number(phone, name, "INVALID_NUMBER")
                    return False
                except NoSuchElementException:
                    # Number is valid if no error message appears
                    pass
                
                # Type message
                message_box.send_keys(message)
                
                # Wait a moment
                time.sleep(1)
                
                # Click send button
                send_button = self.driver.find_element(By.XPATH, '//span[@data-icon="send"]')
                send_button.click()
                
                # Wait for message to send
                time.sleep(3)
                
                # Log success
                logger.info(f"Message sent to {phone} ({name}) ✅")
                self._save_sent_number(phone, name, "SENT")
                return True
                
            except TimeoutException:
                logger.error(f"Timeout waiting for chat to load: {phone} ({name}) ❌")
                self._save_sent_number(phone, name, "TIMEOUT")
                return False
                
            except NoSuchElementException as e:
                logger.error(f"Element not found when sending to {phone} ({name}): {e} ❌")
                self._save_sent_number(phone, name, "ELEMENT_NOT_FOUND")
                return False
                
        except Exception as e:
            logger.error(f"Error sending message to {phone} ({name}): {e} ❌")
            self._save_sent_number(phone, name, "ERROR")
            return False
    
    def process_csv_file(self, csv_file, message_template, delay_range=(10, 30), limit=None):
        """
        Process a CSV file and send messages to all recipients
        
        Args:
            csv_file (str): Path to CSV file
            message_template (str): Message template with placeholders like {name}
            delay_range (tuple): Random delay range in seconds (min, max)
            limit (int): Maximum number of messages to send
            
        Returns:
            tuple: (success_count, failed_count)
        """
        if not os.path.exists(csv_file):
            logger.error(f"CSV file not found: {csv_file}")
            return 0, 0
            
        try:
            # Read the CSV file
            df = pd.read_csv(csv_file)
            
            # Validate required columns
            required_cols = ['phone']
            for col in required_cols:
                if col not in df.columns:
                    logger.error(f"Required column '{col}' not found in CSV")
                    return 0, 0
            
            # Apply limit if specified
            if limit and limit > 0:
                df = df.head(limit)
                
            total = len(df)
            success = 0
            failed = 0
            
            logger.info(f"Starting to process {total} recipients from {csv_file}")
            
            # Process each recipient
            for index, row in df.iterrows():
                phone = str(row['phone']).strip()
                
                # Skip empty phone numbers
                if not phone:
                    logger.warning(f"Empty phone number at row {index+2}, skipping")
                    continue
                    
                # Format phone with country code if needed
                if not phone.startswith('+') and not phone.startswith('91'):
                    phone = '91' + phone
                    
                # Get name if available
                name = str(row.get('name', '')).strip() if 'name' in row else ""
                
                # Personalize message
                personalized_message = message_template
                
                # Replace placeholders in the template
                for col in df.columns:
                    placeholder = '{' + col + '}'
                    if placeholder in message_template:
                        value = str(row.get(col, '')).strip()
                        personalized_message = personalized_message.replace(placeholder, value)
                
                # Send the message
                if self.send_message(phone, personalized_message, name):
                    success += 1
                else:
                    failed += 1
                
                # Print progress
                progress = ((index + 1) / total) * 100
                logger.info(f"Progress: {progress:.1f}% ({index+1}/{total})")
                
                # Add random delay
                if index < total - 1:  # No need to delay after the last message
                    delay = random.uniform(delay_range[0], delay_range[1])
                    logger.info(f"Waiting {delay:.1f} seconds before next message...")
                    time.sleep(delay)
            
            logger.info(f"Completed sending messages. Success: {success}, Failed: {failed}")
            return success, failed
            
        except Exception as e:
            logger.error(f"Error processing CSV file: {e}")
            return 0, 0
    
    def process_filtered_students(self, students_data, message_template, delay_range=(10, 30), limit=None):
        """
        Process a list of student data and send messages
        
        Args:
            students_data (list): List of dictionaries with student data
            message_template (str): Message template with placeholders
            delay_range (tuple): Random delay range in seconds (min, max)
            limit (int): Maximum number of messages to send
            
        Returns:
            tuple: (success_count, failed_count)
        """
        if not students_data:
            logger.error("No student data provided")
            return 0, 0
            
        try:
            # Apply limit if specified
            if limit and limit > 0:
                students_data = students_data[:limit]
                
            total = len(students_data)
            success = 0
            failed = 0
            
            logger.info(f"Starting to process {total} filtered students")
            
            # Process each student
            for index, student in enumerate(students_data):
                phone = str(student.get('phone', '')).strip()
                
                # Skip empty phone numbers
                if not phone:
                    logger.warning(f"Empty phone number for student {index+1}, skipping")
                    continue
                    
                # Format phone with country code if needed
                if not phone.startswith('+') and not phone.startswith('91'):
                    phone = '91' + phone
                    
                name = str(student.get('name', '')).strip()
                
                # Personalize message
                personalized_message = message_template
                
                # Replace placeholders in the template
                for key, value in student.items():
                    placeholder = '{' + key + '}'
                    if placeholder in message_template:
                        personalized_message = personalized_message.replace(placeholder, str(value))
                
                # Send the message
                if self.send_message(phone, personalized_message, name):
                    success += 1
                else:
                    failed += 1
                
                # Print progress
                progress = ((index + 1) / total) * 100
                logger.info(f"Progress: {progress:.1f}% ({index+1}/{total})")
                
                # Add random delay
                if index < total - 1:  # No need to delay after the last message
                    delay = random.uniform(delay_range[0], delay_range[1])
                    logger.info(f"Waiting {delay:.1f} seconds before next message...")
                    time.sleep(delay)
            
            logger.info(f"Completed sending messages. Success: {success}, Failed: {failed}")
            return success, failed
            
        except Exception as e:
            logger.error(f"Error processing filtered students: {e}")
            return 0, 0
    
    def close(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")


def main():
    """Main function to demonstrate the usage"""
    # Example CSV file path
    csv_file = "recipients.csv"
    
    # Example message template with placeholders
    message_template = "Hello {name}, this is a test message for {course} students. Please ignore."
    
    # Initialize WhatsApp automation
    whatsapp = WhatsAppAutomation()
    
    if whatsapp.initialize_driver():
        if whatsapp.login_to_whatsapp():
            # Process the CSV file
            whatsapp.process_csv_file(
                csv_file=csv_file,
                message_template=message_template,
                delay_range=(10, 30),
                limit=5  # Limit to 5 messages for testing
            )
    
    # Always close the driver when done
    whatsapp.close()


if __name__ == "__main__":
    main() 