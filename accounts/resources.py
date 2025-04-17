from import_export import resources
from .models import Company, Job, Student, Application

class CompanyResource(resources.ModelResource):
    class Meta:
        model = Company

class JobResource(resources.ModelResource):
    class Meta:
        model = Job

class StudentResource(resources.ModelResource):
    class Meta:
        model = Student
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'cgpa', 'year', 'course', 
                 'no_of_companies_left', 'bypass_eligibility', 'phone_number', 'gender', 'backlog')
    
class ApplicationResource(resources.ModelResource):
    class Meta:
        model = Application
    
