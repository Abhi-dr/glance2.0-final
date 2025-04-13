import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'glance.settings')
django.setup()

from accounts.models import Student
from django.db import connection

# Check if the column exists
with connection.cursor() as cursor:
    cursor.execute("DESCRIBE accounts_student")
    columns = [col[0] for col in cursor.fetchall()]
    print("Columns in accounts_student table:", columns)
    print("alumni_status in columns:", "alumni_status" in columns)
    print("passout_year in columns:", "passout_year" in columns)

# Try to access the fields
try:
    students = Student.objects.all()
    for student in students:
        print(f"Student: {student.username}")
        print(f"  Alumni Status: {student.alumni_status}")
        print(f"  Passout Year: {student.passout_year}")
except Exception as e:
    print(f"Error: {e}") 