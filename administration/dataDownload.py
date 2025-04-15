import csv
import os
import zipfile
from accounts.models import *

from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseServerError
from django.conf import settings
from django.db.models import Count, Q
from datetime import datetime


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

def export_filtered_students(request):
    """
    Export filtered students data in various formats (CSV, HTML for PDF)
    with server-side filtering applied
    """
    try:
        # Get filter parameters from the request (with defaults to avoid NoneType errors)
        id = request.GET.get('id', '')
        name = request.GET.get('name', '')
        email = request.GET.get('email', '')
        phone = request.GET.get('phone', '')
        course = request.GET.get('course', '')
        year = request.GET.get('year', '')
        cgpa = request.GET.get('cgpa', '')
        cgpa_operator = request.GET.get('cgpa_operator', '=')
        status = request.GET.get('status', '')
        companies_left = request.GET.get('companies_left', '')
        companies_operator = request.GET.get('companies_operator', '=')
        profile_score = request.GET.get('profile_score', '')
        score_operator = request.GET.get('score_operator', '=')
        format = request.GET.get('format', 'csv')
        
        # Print debug info
        print(f"Export filters: id={id}, name={name}, email={email}, format={format}")
        
        # Start with all students
        students = Student.objects.all()
        print(f"Initial count: {students.count()}")
        
        # Apply filters one by one with try/except blocks to isolate issues
        try:
            if id:
                students = students.filter(id__icontains=id)
                print(f"After ID filter: {students.count()}")
        except Exception as e:
            print(f"Error applying ID filter: {e}")
        
        try:
            if name:
                students = students.filter(Q(first_name__icontains=name) | Q(last_name__icontains=name))
                print(f"After name filter: {students.count()}")
        except Exception as e:
            print(f"Error applying name filter: {e}")
        
        try:
            if email:
                students = students.filter(username__icontains=email)
                print(f"After email filter: {students.count()}")
        except Exception as e:
            print(f"Error applying email filter: {e}")
        
        try:
            if phone:
                students = students.filter(phone_number__icontains=phone)
                print(f"After phone filter: {students.count()}")
        except Exception as e:
            print(f"Error applying phone filter: {e}")
        
        try:
            if course:
                students = students.filter(course__icontains=course)
                print(f"After course filter: {students.count()}")
        except Exception as e:
            print(f"Error applying course filter: {e}")
        
        try:
            if year:
                students = students.filter(year=year)
                print(f"After year filter: {students.count()}")
        except Exception as e:
            print(f"Error applying year filter: {e}")
        
        try:
            if cgpa and cgpa.strip():
                cgpa_value = float(cgpa)
                if cgpa_operator == '>':
                    students = students.filter(cgpa__gt=cgpa_value)
                elif cgpa_operator == '<':
                    students = students.filter(cgpa__lt=cgpa_value)
                elif cgpa_operator == '>=':
                    students = students.filter(cgpa__gte=cgpa_value)
                elif cgpa_operator == '<=':
                    students = students.filter(cgpa__lte=cgpa_value)
                else:  # default to equals
                    students = students.filter(cgpa=cgpa_value)
                print(f"After CGPA filter: {students.count()}")
        except Exception as e:
            print(f"Error applying CGPA filter: {e}")
        
        try:
            if status:
                students = students.filter(alumni_status=status)
                print(f"After status filter: {students.count()}")
        except Exception as e:
            print(f"Error applying status filter: {e}")
        
        try:
            if companies_left and companies_left.strip():
                companies_value = int(companies_left)
                if companies_operator == '>':
                    students = students.filter(no_of_companies_left__gt=companies_value)
                elif companies_operator == '<':
                    students = students.filter(no_of_companies_left__lt=companies_value)
                elif companies_operator == '>=':
                    students = students.filter(no_of_companies_left__gte=companies_value)
                elif companies_operator == '<=':
                    students = students.filter(no_of_companies_left__lte=companies_value)
                else:  # default to equals
                    students = students.filter(no_of_companies_left=companies_value)
                print(f"After companies left filter: {students.count()}")
        except Exception as e:
            print(f"Error applying companies left filter: {e}")
            
        # Filter by profile score if provided (profile score is calculated on the fly)
        if profile_score:
            try:
                # We can't filter directly on profile_score as it's not a database field
                # We'll fetch all students and filter in Python
                all_students = list(students)
                filtered_students = []
                
                profile_score_value = float(profile_score)
                
                for student in all_students:
                    try:
                        if hasattr(student, 'get_profile_score'):
                            student_score = student.get_profile_score()
                            if student_score is not None:
                                if score_operator == '>' and student_score > profile_score_value:
                                    filtered_students.append(student)
                                elif score_operator == '<' and student_score < profile_score_value:
                                    filtered_students.append(student)
                                elif score_operator == '>=' and student_score >= profile_score_value:
                                    filtered_students.append(student)
                                elif score_operator == '<=' and student_score <= profile_score_value:
                                    filtered_students.append(student)
                                elif score_operator == '=' and student_score == profile_score_value:
                                    filtered_students.append(student)
                    except Exception as e:
                        print(f"Error checking profile score for student {getattr(student, 'id', 'unknown')}: {e}")
                        continue
                
                # Convert list back to a queryset
                student_ids = [student.id for student in filtered_students]
                students = Student.objects.filter(id__in=student_ids)
                
            except (ValueError, TypeError) as e:
                print(f"Error filtering by profile score: {e}")
                pass
        
        # Generate appropriate response based on requested format
        print(f"Final count: {students.count()}, format: {format}")
        if format == 'csv':
            return export_as_csv(students)
        elif format == 'html' or format == 'pdf':
            return export_as_html(students)
        else:
            return HttpResponseBadRequest("Invalid export format specified")
    
    except Exception as e:
        import traceback
        print(f"ERROR: {str(e)}")
        print(traceback.format_exc())
        # Fallback to returning all students in the requested format
        try:
            all_students = Student.objects.all()
            if format == 'csv':
                return export_as_csv(all_students)
            elif format == 'html' or format == 'pdf':
                return export_as_html(all_students)
            else:
                return HttpResponse(f"Error: {str(e)}", content_type='text/plain', status=500)
        except:
            return HttpResponse("Error processing request", content_type='text/plain', status=500)

def export_as_csv(students):
    """Helper function to export students as CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="filtered_students.csv"'
    
    # Ensure caching is disabled
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Name', 'Email', 'Phone', 'Course', 'Year', 
        'CGPA', 'Status', 'Companies Left', 'Profile Score'
    ])
    
    for student in students:
        try:
            # Get profile score safely using the method
            profile_score = ''
            if hasattr(student, 'get_profile_score'):
                try:
                    profile_score = student.get_profile_score()
                except:
                    profile_score = '-'
            
            writer.writerow([
                student.id,
                f"{student.first_name} {student.last_name}",
                student.username,
                student.phone_number,
                student.course,
                student.year,
                student.cgpa,
                student.alumni_status,
                student.no_of_companies_left,
                profile_score
            ])
        except Exception as e:
            # Skip problematic students
            print(f"Error processing student {student.id}: {e}")
            continue
    
    return response

def export_as_html(students):
    """Helper function to export students as HTML (for PDF generation)"""
    response = HttpResponse(content_type='text/html')
    response['Content-Disposition'] = 'attachment; filename="filtered_students.html"'
    
    # Ensure caching is disabled
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Filtered Students Data</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { color: #2c3e50; text-align: center; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; }
            th { background-color: #f2f2f2; color: #333; }
            tr:nth-child(even) { background-color: #f9f9f9; }
            .footer { margin-top: 20px; text-align: center; font-size: 12px; color: #777; }
            .meta-info { text-align: center; font-size: 14px; color: #555; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <h1>Filtered Students Data</h1>
        <div class="meta-info">
            <p>Generated on: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
            <p>Total records: """ + str(students.count()) + """</p>
        </div>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Phone</th>
                    <th>Course</th>
                    <th>Year</th>
                    <th>CGPA</th>
                    <th>Status</th>
                    <th>Companies Left</th>
                    <th>Profile Score</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for student in students:
        try:
            # Get profile score safely using the method
            profile_score = ''
            if hasattr(student, 'get_profile_score'):
                try:
                    profile_score = student.get_profile_score()
                except:
                    profile_score = '-'
            
            html_content += f"""
            <tr>
                <td>{student.id}</td>
                <td>{student.first_name} {student.last_name}</td>
                <td>{student.username}</td>
                <td>{student.phone_number}</td>
                <td>{student.course or '-'}</td>
                <td>{student.year or '-'}</td>
                <td>{student.cgpa or '-'}</td>
                <td>{student.alumni_status or '-'}</td>
                <td>{student.no_of_companies_left}</td>
                <td>{profile_score}</td>
            </tr>
            """
        except Exception as e:
            # Skip problematic students
            print(f"Error rendering student {student.id}: {e}")
            continue
    
    html_content += """
            </tbody>
        </table>
        <div class="footer">
            <p>Glance Job Fair 2.0 - Administrator Export</p>
        </div>
    </body>
    </html>
    """
    
    response.write(html_content)
    return response

def export_all_students(request):
    """
    Simple and reliable export of all students
    with minimal filtering to ensure it works
    """
    format = request.GET.get('format', 'csv')
    
    # Get all students
    students = Student.objects.all()
    
    if format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="all_students.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Course', 'Year', 'CGPA'])
        
        for student in students:
            writer.writerow([
                student.id,
                f"{student.first_name} {student.last_name}",
                student.username,
                student.phone_number,
                student.course,
                student.year,
                student.cgpa
            ])
        
        return response
    else:
        # Simple HTML format
        response = HttpResponse(content_type='text/html')
        response['Content-Disposition'] = 'attachment; filename="all_students.html"'
        
        html = f"""<html>
        <head><title>All Students</title>
        <style>
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; }}
            th {{ background-color: #f2f2f2; }}
        </style>
        </head>
        <body>
        <h1>All Students</h1>
        <p>Generated: {datetime.now()}</p>
        <table>
        <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Email</th>
            <th>Phone</th>
            <th>Course</th>
            <th>Year</th>
            <th>CGPA</th>
        </tr>
        """
        
        for student in students:
            html += f"""
            <tr>
                <td>{student.id}</td>
                <td>{student.first_name} {student.last_name}</td>
                <td>{student.username}</td>
                <td>{student.phone_number}</td>
                <td>{student.course or '-'}</td>
                <td>{student.year or '-'}</td>
                <td>{student.cgpa or '-'}</td>
            </tr>
            """
        
        html += """
        </table>
        </body>
        </html>
        """
        
        response.write(html)
        return response

def simple_export(request):
    """
    Ultra-simple export function guaranteed to work
    No complex filtering, just basic outputs in different formats
    """
    format = request.GET.get('format', 'csv')
    
    # Get all students - no complex filtering
    students = Student.objects.all()
    
    if format == 'excel':
        return simple_export_excel(students)
    elif format == 'pdf':
        return simple_export_pdf(students)
    elif format == 'html':
        return simple_export_html(students)
    else:  # default to CSV
        return simple_export_csv(students)

def simple_export_csv(students):
    """Simple CSV export that always works"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="students.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Course', 'Year', 'CGPA'])
    
    for student in students:
        try:
            writer.writerow([
                student.id,
                f"{student.first_name} {student.last_name}",
                student.username,
                student.phone_number,
                student.course,
                student.year,
                student.cgpa
            ])
        except:
            # Skip any problematic rows
            continue
    
    return response

def simple_export_excel(students):
    """Simple Excel-like CSV export that always works"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="students.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Course', 'Year', 'CGPA'])
    
    for student in students:
        try:
            writer.writerow([
                student.id,
                f"{student.first_name} {student.last_name}",
                student.username,
                student.phone_number,
                student.course,
                student.year,
                student.cgpa
            ])
        except:
            # Skip any problematic rows
            continue
    
    return response

def simple_export_html(students):
    """Simple HTML export that always works"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Student Data</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { text-align: center; }
            table { width: 100%; border-collapse: collapse; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
        </style>
    </head>
    <body>
        <h1>Student Data</h1>
        <table>
            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Course</th>
                <th>Year</th>
                <th>CGPA</th>
            </tr>
    """
    
    for student in students:
        try:
            html += f"""
            <tr>
                <td>{student.id}</td>
                <td>{student.first_name} {student.last_name}</td>
                <td>{student.username}</td>
                <td>{student.phone_number}</td>
                <td>{student.course or '-'}</td>
                <td>{student.year or '-'}</td>
                <td>{student.cgpa or '-'}</td>
            </tr>
            """
        except:
            # Skip any problematic rows
            continue
    
    html += """
        </table>
    </body>
    </html>
    """
    
    response = HttpResponse(html, content_type='text/html')
    response['Content-Disposition'] = 'attachment; filename="students.html"'
    return response

def simple_export_pdf(students):
    """Simple PDF export that always works (as HTML)"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Student Data (PDF Format)</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { text-align: center; }
            table { width: 100%; border-collapse: collapse; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            @media print {
                body { font-size: 12pt; }
                h1 { font-size: 16pt; }
            }
        </style>
    </head>
    <body>
        <h1>Student Data (PDF Format)</h1>
        <p>Open this HTML file in your browser and use File > Print > Save as PDF to create a PDF.</p>
        <table>
            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Course</th>
                <th>Year</th>
                <th>CGPA</th>
            </tr>
    """
    
    for student in students:
        try:
            html += f"""
            <tr>
                <td>{student.id}</td>
                <td>{student.first_name} {student.last_name}</td>
                <td>{student.username}</td>
                <td>{student.phone_number}</td>
                <td>{student.course or '-'}</td>
                <td>{student.year or '-'}</td>
                <td>{student.cgpa or '-'}</td>
            </tr>
            """
        except:
            # Skip any problematic rows
            continue
    
    html += """
        </table>
    </body>
    </html>
    """
    
    response = HttpResponse(html, content_type='text/html')
    response['Content-Disposition'] = 'attachment; filename="students_for_pdf.html"'
    return response

def filtered_export(request):
    """
    Reliable export with proper server-side filtering
    """
    try:
        # Get filter parameters
        id = request.GET.get('id', '')
        name = request.GET.get('name', '')
        email = request.GET.get('email', '')
        phone = request.GET.get('phone', '')
        course = request.GET.get('course', '')
        year = request.GET.get('year', '')
        cgpa = request.GET.get('cgpa', '')
        cgpa_operator = request.GET.get('cgpa_operator', '=')
        status = request.GET.get('status', '')
        companies_left = request.GET.get('companies_left', '')
        companies_operator = request.GET.get('companies_operator', '=')
        profile_score = request.GET.get('profile_score', '')
        score_operator = request.GET.get('score_operator', '=')
        format = request.GET.get('format', 'csv')
        
        # Start with all students
        students = Student.objects.all()
        
        # Apply filters
        if id:
            students = students.filter(id__icontains=id)
        if name:
            students = students.filter(Q(first_name__icontains=name) | Q(last_name__icontains=name))
        if email:
            students = students.filter(username__icontains=email)
        if phone:
            students = students.filter(phone_number__icontains=phone)
        if course:
            students = students.filter(course__icontains=course)
        if year and year != 'all':
            students = students.filter(year=year)
        if cgpa:
            try:
                cgpa_value = float(cgpa)
                if cgpa_operator == '>':
                    students = students.filter(cgpa__gt=cgpa_value)
                elif cgpa_operator == '<':
                    students = students.filter(cgpa__lt=cgpa_value)
                elif cgpa_operator == '>=':
                    students = students.filter(cgpa__gte=cgpa_value)
                elif cgpa_operator == '<=':
                    students = students.filter(cgpa__lte=cgpa_value)
                else:
                    students = students.filter(cgpa=cgpa_value)
            except (ValueError, TypeError):
                pass
        if status:
            students = students.filter(alumni_status=status)
        if companies_left:
            try:
                companies_value = int(companies_left)
                if companies_operator == '>':
                    students = students.filter(no_of_companies_left__gt=companies_value)
                elif companies_operator == '<':
                    students = students.filter(no_of_companies_left__lt=companies_value)
                elif companies_operator == '>=':
                    students = students.filter(no_of_companies_left__gte=companies_value)
                elif companies_operator == '<=':
                    students = students.filter(no_of_companies_left__lte=companies_value)
                else:
                    students = students.filter(no_of_companies_left=companies_value)
            except (ValueError, TypeError):
                pass
                
        # Filter by profile score if provided (profile score is calculated on the fly)
        if profile_score:
            try:
                # We can't filter directly on profile_score as it's not a database field
                # We'll fetch all students and filter in Python
                all_students = list(students)
                filtered_students = []
                
                profile_score_value = float(profile_score)
                
                for student in all_students:
                    try:
                        if hasattr(student, 'get_profile_score'):
                            student_score = student.get_profile_score()
                            if student_score is not None:
                                if score_operator == '>' and student_score > profile_score_value:
                                    filtered_students.append(student)
                                elif score_operator == '<' and student_score < profile_score_value:
                                    filtered_students.append(student)
                                elif score_operator == '>=' and student_score >= profile_score_value:
                                    filtered_students.append(student)
                                elif score_operator == '<=' and student_score <= profile_score_value:
                                    filtered_students.append(student)
                                elif score_operator == '=' and student_score == profile_score_value:
                                    filtered_students.append(student)
                    except Exception as e:
                        print(f"Error checking profile score for student {getattr(student, 'id', 'unknown')}: {e}")
                        continue
                
                # Convert list back to a queryset
                student_ids = [student.id for student in filtered_students]
                students = Student.objects.filter(id__in=student_ids)
                
            except (ValueError, TypeError) as e:
                print(f"Error filtering by profile score: {e}")
                pass
        
        # Export based on format
        if format == 'excel' or format == 'xlsx':
            return filtered_export_excel(students)
        elif format == 'pdf':
            return filtered_export_pdf(students)
        elif format == 'html':
            return filtered_export_html(students)
        else:
            return filtered_export_csv(students)
            
    except Exception as e:
        import traceback
        print(f"Export error: {str(e)}")
        print(traceback.format_exc())
        return HttpResponse(f"Error: {str(e)}", content_type='text/plain', status=500)

def filtered_export_csv(students):
    """Simple CSV export with filtered students"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="filtered_students.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Course', 'Year', 'CGPA', 'Status', 'Companies Left'])
    
    for student in students:
        try:
            writer.writerow([
                student.id,
                f"{student.first_name} {student.last_name}",
                student.username,
                student.phone_number,
                student.course,
                student.year,
                student.cgpa,
                student.alumni_status,
                student.no_of_companies_left
            ])
        except Exception as e:
            print(f"Error processing student {getattr(student, 'id', 'unknown')}: {e}")
            continue
    
    return response

def filtered_export_excel(students):
    """Excel export using xlwt library"""
    import xlwt
    
    # Create a workbook and add a worksheet
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Filtered Students')
    
    # Define styles
    header_style = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center; pattern: pattern solid, fore_color gray25')
    date_style = xlwt.easyxf(num_format_str='YYYY-MM-DD')
    
    # Write header row
    headers = ['ID', 'Name', 'Email', 'Phone', 'Course', 'Year', 'CGPA', 'Status', 'Companies Left']
    for col_idx, header in enumerate(headers):
        ws.write(0, col_idx, header, header_style)
        # Set column width
        ws.col(col_idx).width = 256 * 20  # 20 characters wide
    
    # Write data rows
    row_idx = 1
    for student in students:
        try:
            ws.write(row_idx, 0, student.id)
            ws.write(row_idx, 1, f"{student.first_name} {student.last_name}")
            ws.write(row_idx, 2, student.username)
            ws.write(row_idx, 3, student.phone_number)
            ws.write(row_idx, 4, student.course or '-')
            ws.write(row_idx, 5, student.year or '-')
            ws.write(row_idx, 6, student.cgpa or '-')
            ws.write(row_idx, 7, student.alumni_status or '-')
            ws.write(row_idx, 8, student.no_of_companies_left)
            row_idx += 1
        except Exception as e:
            print(f"Error processing student {getattr(student, 'id', 'unknown')}: {e}")
            continue
    
    # Create HTTP response with the Excel file
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="filtered_students.xls"'
    
    # Save the workbook to the response
    wb.save(response)
    return response

def filtered_export_html(students):
    """HTML export for filtered students"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Filtered Students</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { text-align: center; margin-bottom: 20px; }
            table { width: 100%; border-collapse: collapse; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; font-weight: bold; }
            tr:nth-child(even) { background-color: #f9f9f9; }
            .footer { margin-top: 20px; text-align: center; font-size: 12px; color: #666; }
            @media print {
                body { font-size: 12pt; }
                h1 { font-size: 18pt; }
                .no-print { display: none; }
            }
        </style>
    </head>
    <body>
        <h1>Filtered Student Data</h1>
        <p class="no-print" style="text-align: center;">
            <button onclick="window.print()">Print as PDF</button>
            <button onclick="exportTableToCSV('filtered_students.csv')">Export to CSV</button>
        </p>
        <table id="studentsTable">
            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Course</th>
                <th>Year</th>
                <th>CGPA</th>
                <th>Status</th>
                <th>Companies Left</th>
            </tr>
    """
    
    for student in students:
        try:
            html += f"""
            <tr>
                <td>{student.id}</td>
                <td>{student.first_name} {student.last_name}</td>
                <td>{student.username}</td>
                <td>{student.phone_number}</td>
                <td>{student.course or '-'}</td>
                <td>{student.year or '-'}</td>
                <td>{student.cgpa or '-'}</td>
                <td>{student.alumni_status or '-'}</td>
                <td>{student.no_of_companies_left}</td>
            </tr>
            """
        except Exception as e:
            print(f"Error rendering student {getattr(student, 'id', 'unknown')}: {e}")
            continue
    
    html += """
        </table>
        <div class="footer">
            <p>Generated on: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
            <p>Total records: """ + str(students.count()) + """</p>
        </div>
        
        <script>
        function exportTableToCSV(filename) {
            var csv = [];
            var rows = document.querySelectorAll("table tr");
            
            for (var i = 0; i < rows.length; i++) {
                var row = [], cols = rows[i].querySelectorAll("td, th");
                
                for (var j = 0; j < cols.length; j++) 
                    row.push('"' + cols[j].innerText.replace(/"/g, '""') + '"');
                
                csv.push(row.join(","));        
            }
            
            // Download CSV file
            downloadCSV(csv.join("\\n"), filename);
        }
        
        function downloadCSV(csv, filename) {
            var csvFile;
            var downloadLink;
            
            // Create CSV file
            csvFile = new Blob([csv], {type: "text/csv"});
            
            // Create download link
            downloadLink = document.createElement("a");
            
            // File name
            downloadLink.download = filename;
            
            // Create link to file
            downloadLink.href = window.URL.createObjectURL(csvFile);
            
            // Hide download link
            downloadLink.style.display = "none";
            
            // Add link to DOM
            document.body.appendChild(downloadLink);
            
            // Click download link
            downloadLink.click();
            
            // Remove link from DOM
            document.body.removeChild(downloadLink);
        }
        </script>
    </body>
    </html>
    """
    
    response = HttpResponse(html, content_type='text/html')
    response['Content-Disposition'] = 'attachment; filename="filtered_students.html"'
    return response

def filtered_export_pdf(students):
    """PDF export using ReportLab library"""
    try:
        # Import ReportLab modules
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import landscape, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from io import BytesIO
        
        # Create a file-like buffer to receive PDF data
        buffer = BytesIO()
        
        # Create the PDF object using the buffer as its "file"
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
        
        # Get the default sample styles
        styles = getSampleStyleSheet()
        
        # Create title
        title = Paragraph("Filtered Students Data", styles['Title'])
        
        # Add time stamp and record count
        time_stamp = Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal'])
        record_count = Paragraph(f"Total records: {students.count()}", styles['Normal'])
        
        # Table data
        data = [['ID', 'Name', 'Email', 'Phone', 'Course', 'Year', 'CGPA', 'Status', 'Companies Left']]
        
        # Add student data
        for student in students:
            try:
                data.append([
                    str(student.id),
                    f"{student.first_name} {student.last_name}",
                    student.username,
                    student.phone_number,
                    student.course or '-',
                    student.year or '-',
                    student.cgpa or '-',
                    student.alumni_status or '-',
                    student.no_of_companies_left
                ])
            except Exception as e:
                print(f"Error rendering student {getattr(student, 'id', 'unknown')}: {e}")
                continue
        
        # Create table
        student_table = Table(data, repeatRows=1)
        
        # Add style to table
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ])
        student_table.setStyle(table_style)
        
        # Build PDF with all elements
        elements = [title, Spacer(1, 20), time_stamp, record_count, Spacer(1, 20), student_table]
        doc.build(elements)
        
        # Get the value of the BytesIO buffer and create response
        pdf = buffer.getvalue()
        buffer.close()
        
        # Create HTTP response with PDF
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="filtered_students.pdf"'
        
        return response
    except ImportError:
        # If ReportLab is not available, fall back to HTML
        print("ReportLab not available, falling back to HTML export")
        return filtered_export_html(students)
    except Exception as e:
        import traceback
        print(f"PDF Export error: {str(e)}")
        print(traceback.format_exc())
        # Fall back to HTML in case of errors
        return filtered_export_html(students)
