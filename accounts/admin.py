from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .resources import CompanyResource, JobResource, StudentResource, ApplicationResource
from .models import Company, Job, Student, Application, Notification, Administrator, AlumniRegistration, Volunteer, Attendance


# Customize the admin site header, title, and index title
admin.site.site_header = "GLANCE Job Fair Admin"
admin.site.site_title = "GLANCE Admin Portal"
admin.site.index_title = "Welcome to GLANCE Admin Portal"


class StudentAdmin(ImportExportModelAdmin):
    resource_class = StudentResource
    list_display = ('username', 'year', 'cgpa', "no_of_companies_left")
    list_filter = ('year', "no_of_companies_left")
    search_fields = ('username', 'first_name', 'last_name', 'email', 'course')

class AdministratorAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'phone_number')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone_number')

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'timeStamp')
    search_fields = ('title', 'description')
    list_filter = ('timeStamp',)

class CompanyAdmin(ImportExportModelAdmin):
    resource_class = CompanyResource
    list_display = ('name', 'location', 'size', 'website')
    search_fields = ('name', 'location', 'description')
    list_filter = ('size',)

class JobAdmin(ImportExportModelAdmin):
    resource_class = JobResource
    list_display = ('title', 'company', 'interview_date', 'interview_mode',
                    'deadline', 'cgpa_criteria', 'no_of_openings', 'job_type')
    search_fields = ('title', 'company__name', 'role', 'description')
    list_filter = ('interview_date', 'job_type', 'company')


class ApplicationAdmin(ImportExportModelAdmin):
    resource_class = ApplicationResource
    list_display = ('student', 'job', 'application_date', 'status')
    search_fields = ('student__first_name', 'student__last_name',
                     'student__email', 'job__title', 'job__company__name')
    list_filter = ('status', 'job__interview_date', 'job__company')
    
    list_per_page = 3000


class VolunteerAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'phone_number')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone_number')


class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('application', 'is_present', 'marked_by', 'marked_at')
    search_fields = ('application__student__first_name', 'application__student__last_name',
                     'application__job__company__name', 'application__job__title')
    list_filter = ('is_present', 'marked_at', 'application__job__interview_date')


class AlumniRegistrationAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone_number',
                    'company', 'designation', 'passout_year')
    search_fields = ('name', 'email', 'phone_number',
                     'company', 'designation')
    list_filter = ('passout_year',)


admin.site.register(Company, CompanyAdmin)
admin.site.register(Job, JobAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(Administrator, AdministratorAdmin)
admin.site.register(Application, ApplicationAdmin)
admin.site.register(Volunteer, VolunteerAdmin)
admin.site.register(Attendance, AttendanceAdmin)
admin.site.register(AlumniRegistration, AlumniRegistrationAdmin)
admin.site.register(Notification, NotificationAdmin)