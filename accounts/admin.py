from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .resources import CompanyResource, JobResource, StudentResource, ApplicationResource
from .models import Company, Job, Student, Application, Notification


class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'timeStamp')
    search_fields = ('title', 'description')

class CompanyAdmin(ImportExportModelAdmin):
    resource_class = CompanyResource
    list_display = ('name', 'location')
    search_fields = ('name', 'location')

class JobAdmin(ImportExportModelAdmin):
    resource_class = JobResource
    list_display = ('title', 'company', "interview_date")
    list_filter = ('company', "interview_date")
    search_fields = ('title', 'description', 'requirements')

class StudentAdmin(ImportExportModelAdmin):
    resource_class = StudentResource
    list_display = ('username', 'year', 'cgpa', "no_of_companies_left")
    list_filter = ('year', "no_of_companies_left")
    search_fields = ('first_name', 'last_name', 'username', "year", "phone_number")
    exclude = ('email', 'password', 'last_login', 'is_superuser', 'groups', 'user_permissions', 'is_staff', 'is_active', 'date_joined')

class ApplicationAdmin(ImportExportModelAdmin):
    resource_class = ApplicationResource
    list_display = ('student', 'job', 'status')
    list_filter = ('status', "job")
    search_fields = ('student', 'job', "student")
    
    list_per_page = 3000


admin.site.register(Company, CompanyAdmin)
admin.site.register(Job, JobAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(Application, ApplicationAdmin)
admin.site.register(Notification)