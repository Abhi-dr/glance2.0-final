# WhatsApp Bulk Messaging Automation

This feature allows you to send personalized WhatsApp messages to filtered students using Selenium automation.

## Setup Instructions

### 1. Install Required Packages

```bash
pip install -r whatsapp_requirements.txt
```

### 2. Download ChromeDriver

The automation requires ChromeDriver that matches your Chrome browser version:

1. Check your Chrome version by navigating to `chrome://version` in Chrome
2. Download the corresponding ChromeDriver from [https://chromedriver.chromium.org/downloads](https://chromedriver.chromium.org/downloads)
3. Extract the ChromeDriver executable to a known location

## Usage Options

### Option 1: Using the Web Interface

1. Navigate to the WhatsApp Messages page in the administration section
2. Use the filters to select the students you want to message
3. Compose your message using the template feature
4. Choose one of the following options:
   - **Send WhatsApp Messages**: Opens individual WhatsApp Web links for each student
   - **Export to CSV**: Downloads a CSV file with student data for use with the automation script
   - **Show Automation Command**: Displays the command to run the automation script with current filters

### Option 2: Using the Management Command

Run the Django management command directly from the command line:

```bash
python manage.py send_whatsapp_bulk --message "Hello {{name}}, this is a reminder about your interview tomorrow." --filter-json '{"course":"B.Tech","attendance_status":"present"}'
```

#### Command Options

- `--message`: Message template with placeholders like `{{name}}`, `{{course}}`, etc.
- `--csv`: Path to CSV file with recipient data (alternative to filters)
- `--delay-min`: Minimum delay between messages in seconds (default: 10)
- `--delay-max`: Maximum delay between messages in seconds (default: 30)
- `--limit`: Maximum number of messages to send
- `--chrome-data-dir`: Chrome user data directory to use for session persistence
- `--chromedriver`: Path to chromedriver executable
- `--test-mode`: Run without actually sending messages
- Filter options:
  - `--id`: Filter by student ID
  - `--name`: Filter by student name
  - `--email`: Filter by student email
  - `--phone`: Filter by student phone number
  - `--course`: Filter by course
  - `--year`: Filter by year
  - `--company`: Filter by company applied
  - `--attendance`: Filter by attendance status (present, absent, not_marked)
  - `--filter-json`: JSON string with filter parameters

## Examples

### Basic Usage

```bash
python manage.py send_whatsapp_bulk --message "Hello {{name}}, please confirm your attendance for {{company}} interview tomorrow." --course "B.Tech" --test-mode
```

### With Multiple Filters

```bash
python manage.py send_whatsapp_bulk --message "Hello {{name}}, this is a reminder about your interview." --filter-json '{"course":"B.Tech","year":"3rd Year","attendance_status":"present"}'
```

### Using a CSV File

```bash
python manage.py send_whatsapp_bulk --message "Hello {{name}}, this is a reminder." --csv "exported_students.csv" --delay-min 15 --delay-max 45
```

### With Chrome User Data Directory (for Session Persistence)

```bash
python manage.py send_whatsapp_bulk --message "Hello {{name}}" --name "John" --chrome-data-dir "/path/to/chrome/profile" --chromedriver "/path/to/chromedriver"
```

## CSV File Format

If you're using a CSV file, it should have the following columns:

- `phone` (required): Phone number with country code
- `name` (optional): Student name
- Other columns can be used as placeholders in the message template

Example CSV:

```
id,name,phone,email,course,year
1,John Doe,+919876543210,john@example.com,B.Tech,3rd Year
2,Jane Smith,+919876543211,jane@example.com,BBA,2nd Year
```

## Safety Tips

1. Always use `--test-mode` first to see what messages would be sent without actually sending them
2. Start with a small `--limit` value (e.g., 5-10) to test the process
3. Use reasonable delays (10-30 seconds) to avoid being flagged by WhatsApp
4. Consider spreading large campaigns across multiple days to stay within WhatsApp's rate limits
5. Always review the list of recipients before sending real messages

## Troubleshooting

- **QR Code Not Scanning**: Make sure your phone's WhatsApp account is active and connected to the internet
- **Chrome Crashes**: Try using a dedicated Chrome user data directory with `--chrome-data-dir`
- **Messages Not Sending**: Check phone number formats (should include country code)
