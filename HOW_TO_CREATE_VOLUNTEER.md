# How to Create Volunteer Accounts in GLANCE 2.0

## Problem:

The volunteer dashboard was not showing data because there were no volunteer accounts created in the system.

## Solution:

A management command has been created to easily add volunteer users to the system. This command allows you to create volunteer accounts with all the necessary information.

## How to Create a Volunteer User:

1. Open a terminal/command prompt in the root directory of the project.

2. Run the following command (replace the placeholder values with actual data):

```
python manage.py create_volunteer --username volunteer@example.com --email volunteer@example.com --password YourSecurePassword --first_name "First" --last_name "Last" --phone "1234567890" --gender "Male"
```

### Parameters:

- `--username`: The username for the volunteer (typically their email address)
- `--email`: The email address of the volunteer
- `--password`: A secure password
- `--first_name`: The volunteer's first name
- `--last_name`: The volunteer's last name
- `--phone`: The volunteer's phone number (10 digits)
- `--gender`: Gender of the volunteer (Male/Female/Prefer not to say)

### Example:

```
python manage.py create_volunteer --username john.doe@gla.ac.in --email john.doe@gla.ac.in --password SecurePassword123! --first_name "John" --last_name "Doe" --phone "9876543210" --gender "Male"
```

## After Creating a Volunteer:

1. The volunteer can now log in using their credentials at the login page.
2. They will be automatically redirected to the volunteer dashboard.
3. They will have access to manage attendances and applications.

## Note:

The volunteer account has staff privileges, which means they can access the admin interface but don't have full superuser permissions. This is designed to give them the appropriate level of access for their role.

If you need to create multiple volunteers, simply run the command multiple times with different credentials.
