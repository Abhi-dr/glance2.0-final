import csv
import os
import zipfile
from accounts.models import *

from django.http import HttpResponse
from django.conf import settings
from django.db.models import Count


def export_unapplied_students_csv(request):
    # Query all students who have registered but not applied to any company
    unapplied_students = Student.objects.filter(application__isnull=True)
    
    # Define the CSV file response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="unapplied_students.csv"'

    # Create a CSV writer
    writer = csv.writer(response)
    
    # Write the header row
    writer.writerow(['First Name', 'Last Name', 'Email', 'Phone Number', 'Gender', 'Course', 'Year', 'CGPA'])

    # Write data rows
    for student in unapplied_students:
        
        if (student.course == "B.Tech" or student.course == "BBA"):
            if (student.year == "1st Year"):
                continue
        writer.writerow([student.first_name, student.last_name, student.username, student.phone_number, student.gender, student.course, student.year, student.cgpa])
        
    return response

# =============


def export_uneligible_sutents(request):
    # Query all students who have registered but not applied to any company
    unapplied_students = Student.objects.filter(application__isnull=True)
    
    # Define the CSV file response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="unapplied_students.csv"'

    # Create a CSV writer
    writer = csv.writer(response)
    
    # Write the header row
    writer.writerow(['First Name', 'Last Name', 'Email', 'Phone Number', 'Gender', 'Course', 'Year', 'CGPA'])

    # Write data rows
    for student in unapplied_students:
        
        if (student.course == "B.Tech" or student.course == "BBA"):
            if (student.year == "1st Year"):
                continue
        writer.writerow([student.first_name, student.last_name, student.username, student.phone_number, student.gender, student.course, student.year, student.cgpa])
        
    return response

# ==============

def export_uneligible_students(request):
    # Query all students who have registered but not applied to any company
    uneligible_students_btech = Student.objects.filter(application__isnull=True, course = "B.Tech", year = "1st Year")
    uneligible_students_bba = Student.objects.filter(application__isnull=True, course = "BBA", year = "1st Year")
    
    
    uneligible_students = uneligible_students_btech.union(uneligible_students_bba)
    
    
    
    # Define the CSV file response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="unapplied_students.csv"'

    # Create a CSV writer
    writer = csv.writer(response)
    
    # Write the header row
    writer.writerow(['First Name', 'Last Name', 'Email', 'Phone Number', 'Gender', 'Course', 'Year', 'CGPA'])

    # Write data rows
    for student in uneligible_students:
        writer.writerow([student.first_name, student.last_name, student.username, student.phone_number, student.gender, student.course, student.year, student.cgpa])
        
    return response



# ===========

def export_company_applications_summary_csv(request):
    # Get all companies with the total number of applications for each company
    companies_with_applications_count = Company.objects.annotate(total_applications=Count('jobs__applications'))

    # Define the CSV file response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="company_applications_summary.csv"'

    # Create a CSV writer
    writer = csv.writer(response)

    # Write the header row
    writer.writerow(['Company Name', 'Interview Date', 'Interview Mode', 'Total Applications'])

    # Write data rows
    for company in companies_with_applications_count:
        # Get all jobs for the current company
        jobs = Job.objects.filter(company=company)

        # Iterate over each job and write its details along with total applications
        for job in jobs:
            writer.writerow([company.name, job.interview_date, job.interview_mode, company.total_applications])

    return response

# ================================ DOWNLOAD APPLICATIONS =================

def export_job_applications_csv(request, job_id):
    # Get the job object
    job = Job.objects.get(id=job_id)

    # Get all applications for the job
    applications = Application.objects.filter(job=job)

    # Define the CSV file response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{job.title}_applications.csv"'

    # Create a CSV writer
    writer = csv.writer(response)

    # Write the header row
    writer.writerow(['Student Name', 'Email', 'Course', "Year", 'Highschool', "Intermediate", "CGPA", "LinkedIn", "Github"])

    # Write data rows
    for application in applications:
        writer.writerow([application.student.first_name + " " + application.student.last_name, application.student.username, application.student.course, application.student.year, application.application_date, application.student.tenth, application.student.twelfth, application.student.cgpa, application.student.linkedin_id, application.student.github_id])

    return response


def download_job_resumes(request, job_id):
    # Get the job object
    job = Job.objects.get(id=job_id)

    # Get all applications for the job
    applications = Application.objects.filter(job=job)

    # Create a ZIP file
    zip_file_path = os.path.join(settings.MEDIA_ROOT, 'job_resumes.zip')
    with zipfile.ZipFile(zip_file_path, 'w') as zipf:
        for application in applications:
            if application.student.resume:
                resume_path = application.student.resume.path
                zipf.write(resume_path, os.path.basename(resume_path))

    # Create a response to download the ZIP file
    response = HttpResponse(content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{job.title}_resumes.zip"'

    # Write the ZIP file content to the response
    with open(zip_file_path, 'rb') as zipf:
        response.write(zipf.read())

    # Delete the temporary ZIP file
    os.remove(zip_file_path)

    return response

# ================ Download the resumes of all the applicants whose course is either BBA or MBA

def download_resumes(request):
    # Get all students whose course is either BBA or MBA
    students = Student.objects.filter(course__in=['BBA', 'MBA'])

    # Create a ZIP file
    zip_file_path = os.path.join(settings.MEDIA_ROOT, 'resumes.zip')
    with zipfile.ZipFile(zip_file_path, 'w') as zipf:
        for student in students:
            if student.resume:
                resume_path = student.resume.path
                zipf.write(resume_path, os.path.basename(resume_path))

    # Create a response to download the ZIP file
    response = HttpResponse(content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="resumes.zip"'

    # Write the ZIP file content to the response
    with open(zip_file_path, 'rb') as zipf:
        response.write(zipf.read())

    # Delete the temporary ZIP file
    os.remove(zip_file_path)

    return response
