import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'glance.settings')
django.setup()

from accounts.models import Student

# Update all students to have 3 companies left
updated_count = Student.objects.update(no_of_companies_left=3)

print(f"Updated {updated_count} students to have 3 companies left.")

# Verify the update
students = Student.objects.all()
for student in students:
    print(f"Student: {student.username}, Companies left: {student.no_of_companies_left}") 