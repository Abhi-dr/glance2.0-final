import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'glance.settings')
django.setup()

from accounts.models import Student

students = Student.objects.all()
for student in students:
    print(f"Student: {student.username}, Companies left: {student.no_of_companies_left}") 