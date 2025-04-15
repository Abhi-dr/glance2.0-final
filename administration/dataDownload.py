import csv
import os
import zipfile
from accounts.models import *

from django.http import HttpResponse
from django.conf import settings
from django.db.models import Count
from datetime import datetime
from django.db.models import Q


def export_unapplied_students_csv(request):
    # Query all students who have registered but not applied to any company
    unapplied_students = Student.objects.filter(application__isnull=True)
    
    # Define the CSV file response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="unapplied_students.csv"'
    # Ensure caching is disabled
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

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
    # Ensure caching is disabled
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

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
    response['Content-Disposition'] = 'attachment; filename="uneligible_students.csv"'
    # Ensure caching is disabled
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

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
    # Ensure caching is disabled
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

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

# =========== PDF Export ==========

def export_filtered_students_pdf(request):
    """
    Create a simplified PDF version of student data
    This is a fallback for when client-side PDF generation fails
    """
    try:
        # Get filtered students (simplified version - just getting all students)
        students = Student.objects.all().order_by('-id')[:100]  # Limit to 100 students
        
        # Create a simple HTML-based PDF response
        html_content = """
        <html>
        <head>
            <title>Student Data Export</title>
            <style>
                body { font-family: Arial, sans-serif; }
                table { width: 100%; border-collapse: collapse; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                .header { text-align: center; margin-bottom: 20px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Student Data Export</h1>
                <p>Generated on: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Course</th>
                        <th>Year</th>
                        <th>CGPA</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        # Add student rows
        for student in students:
            html_content += f"""
                <tr>
                    <td>{student.id}</td>
                    <td>{student.first_name} {student.last_name}</td>
                    <td>{student.username}</td>
                    <td>{student.course or '-'}</td>
                    <td>{student.year or '-'}</td>
                    <td>{student.cgpa or '-'}</td>
                </tr>
            """
        
        # Close the HTML
        html_content += """
                </tbody>
            </table>
        </body>
        </html>
        """
        
        # For a real implementation, you'd use a PDF library like WeasyPrint or xhtml2pdf
        # But for now, we'll just return the HTML as a simple solution
        response = HttpResponse(html_content)
        response['Content-Type'] = 'text/html'
        response['Content-Disposition'] = 'attachment; filename="student_data.html"'
        
        # Ensure caching is disabled
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        return response
    except Exception as e:
        # If something goes wrong, fall back to CSV
        print(f"Error in PDF export: {e}")
        return export_company_applications_summary_csv(request)

# ================================ DOWNLOAD APPLICATIONS =================

def export_job_applications_csv(request, job_id):
    # Get the job object
    job = Job.objects.get(id=job_id)

    # Get all applications for the job
    applications = Application.objects.filter(job=job)

    # Define the CSV file response
    response = HttpResponse(content_type='text/csv')
    safe_filename = job.title.replace(" ", "_").replace("/", "-")
    response['Content-Disposition'] = f'attachment; filename="{safe_filename}_applications.csv"'
    # Ensure caching is disabled
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

    # Create a CSV writer
    writer = csv.writer(response)

    # Write the header row
    writer.writerow(['Student Name', 'Email', 'Course', "Year", 'Application Date', "Highschool", "Intermediate", "CGPA", "LinkedIn", "Github"])

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
    safe_filename = job.title.replace(" ", "_").replace("/", "-")
    response['Content-Disposition'] = f'attachment; filename="{safe_filename}_resumes.zip"'
    # Ensure caching is disabled
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

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
    response['Content-Disposition'] = 'attachment; filename="student_resumes.zip"'
    # Ensure caching is disabled
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

    # Write the ZIP file content to the response
    with open(zip_file_path, 'rb') as zipf:
        response.write(zipf.read())

    # Delete the temporary ZIP file
    os.remove(zip_file_path)

    return response

# =========== Server-Side Filtered Export ==========

def export_filtered_students(request):
    """
    Export students data with server-side filtering based on request parameters
    Supports CSV, Excel-compatible CSV, and HTML formats
    """
    # Get filter parameters from request
    filter_params = {}
    format_type = request.GET.get('format', 'csv')
    
    # Extract all possible filter parameters
    id_filter = request.GET.get('id', '')
    name_filter = request.GET.get('name', '')
    email_filter = request.GET.get('email', '')
    phone_filter = request.GET.get('phone', '')
    course_filter = request.GET.get('course', '')
    year_filter = request.GET.get('year', '')
    cgpa_filter = request.GET.get('cgpa', '')
    cgpa_operator = request.GET.get('cgpa_operator', '=')
    status_filter = request.GET.get('status', '')
    companies_left_filter = request.GET.get('companies_left', '')
    companies_operator = request.GET.get('companies_operator', '=')
    
    # Start with all students
    students_query = Student.objects.all()
    
    # Apply filters
    if id_filter:
        students_query = students_query.filter(id=id_filter)
    
    if name_filter:
        students_query = students_query.filter(
            Q(first_name__icontains=name_filter) | 
            Q(last_name__icontains=name_filter)
        )
    
    if email_filter:
        students_query = students_query.filter(username__icontains=email_filter)
    
    if phone_filter:
        students_query = students_query.filter(phone_number__icontains=phone_filter)
    
    if course_filter:
        students_query = students_query.filter(course=course_filter)
    
    if year_filter:
        students_query = students_query.filter(year=year_filter)
    
    if cgpa_filter:
        try:
            cgpa_value = float(cgpa_filter)
            if cgpa_operator == '=':
                students_query = students_query.filter(cgpa=cgpa_value)
            elif cgpa_operator == '>':
                students_query = students_query.filter(cgpa__gt=cgpa_value)
            elif cgpa_operator == '<':
                students_query = students_query.filter(cgpa__lt=cgpa_value)
            elif cgpa_operator == '>=':
                students_query = students_query.filter(cgpa__gte=cgpa_value)
            elif cgpa_operator == '<=':
                students_query = students_query.filter(cgpa__lte=cgpa_value)
        except (ValueError, TypeError):
            pass
    
    if status_filter:
        students_query = students_query.filter(alumni_status=status_filter)
    
    if companies_left_filter:
        try:
            companies_value = int(companies_left_filter)
            if companies_operator == '=':
                students_query = students_query.filter(no_of_companies_left=companies_value)
            elif companies_operator == '>':
                students_query = students_query.filter(no_of_companies_left__gt=companies_value)
            elif companies_operator == '<':
                students_query = students_query.filter(no_of_companies_left__lt=companies_value)
            elif companies_operator == '>=':
                students_query = students_query.filter(no_of_companies_left__gte=companies_value)
            elif companies_operator == '<=':
                students_query = students_query.filter(no_of_companies_left__lte=companies_value)
        except (ValueError, TypeError):
            pass
    
    # Get ordered students (limited to 1000 for performance)
    students = students_query.order_by('-id')[:1000]
    
    # Prepare response based on format type
    if format_type == 'excel':
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="filtered_students.xls"'
        content_type = 'application/vnd.ms-excel'
        filename = 'filtered_students.xls'
    elif format_type == 'html':
        response = HttpResponse(content_type='text/html')
        response['Content-Disposition'] = 'attachment; filename="filtered_students.html"'
        content_type = 'text/html'
        filename = 'filtered_students.html'
    else:  # Default to CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="filtered_students.csv"'
        content_type = 'text/csv'
        filename = 'filtered_students.csv'
    
    # Ensure caching is disabled
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    if format_type == 'html':
        # Create HTML content
        html_content = """
        <html>
        <head>
            <title>Filtered Students Export</title>
            <style>
                body { font-family: Arial, sans-serif; }
                table { width: 100%; border-collapse: collapse; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                .header { text-align: center; margin-bottom: 20px; }
                tr:nth-child(even) { background-color: #f9f9f9; }
                tr:hover { background-color: #f1f1f1; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Filtered Students Export</h1>
                <p>Generated on: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
                <p>Total Records: """ + str(len(students)) + """</p>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Phone Number</th>
                        <th>Course</th>
                        <th>Year</th>
                        <th>CGPA</th>
                        <th>Status</th>
                        <th>Companies Left</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        # Add student rows
        for student in students:
            html_content += f"""
                <tr>
                    <td>{student.id}</td>
                    <td>{student.first_name} {student.last_name}</td>
                    <td>{student.username}</td>
                    <td>{student.phone_number or '-'}</td>
                    <td>{student.course or '-'}</td>
                    <td>{student.year or '-'}</td>
                    <td>{student.cgpa or '-'}</td>
                    <td>{student.alumni_status or 'Current Student'}</td>
                    <td>{student.no_of_companies_left}</td>
                </tr>
            """
        
        # Close the HTML
        html_content += """
                </tbody>
            </table>
        </body>
        </html>
        """
        
        response.write(html_content)
    else:
        # Create CSV writer
        writer = csv.writer(response)
        
        # Write header row
        writer.writerow(['ID', 'Name', 'Email', 'Phone Number', 'Course', 'Year', 'CGPA', 'Status', 'Companies Left'])
        
        # Write data rows
        for student in students:
            writer.writerow([
                student.id,
                f"{student.first_name} {student.last_name}",
                student.username,
                student.phone_number or '',
                student.course or '',
                student.year or '',
                student.cgpa or '',
                student.alumni_status or 'Current Student',
                student.no_of_companies_left
            ])
    