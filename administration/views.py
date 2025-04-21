from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from accounts.models import Company, Job, Student, Application, Notification, Administrator
from django.db.models import Q, Count, Sum, Avg, F, ExpressionWrapper, BooleanField, Case, When, Value, IntegerField
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.db import models
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import json
from datetime import datetime, timedelta
import csv
import os
from django.conf import settings

import threading

from django.core.mail import send_mail

import requests

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.http import JsonResponse

# Custom decorator that allows administrators to access pages
def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            # Check if user is staff or is an administrator
            if request.user.is_staff or hasattr(request.user, 'administrator'):
                return view_func(request, *args, **kwargs)
        # Redirect to login page if not authenticated or not an admin
        return redirect('login')
    return wrapper

# Comment out the external API email functions
"""
def send_email_async(to, subject, text):
    url = 'https://send-mail-api-express.onrender.com/send-email'
    # url = "http://localhost:3000/send-email"

    data = {
        'to': to,
        'subject': subject,
        'text': text
    }
    response = requests.post(url, json=data)
    response.raise_for_status()
    print("Email sent successfully:", response.json().get("message"))
    return True

def send_emails_threaded(recipients, subject, text):
    threads = []
    for recipient in recipients:
        thread = threading.Thread(target=send_email_async, args=(recipient, subject, text))
        thread.start()
        threads.append(thread)
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    print("All emails sent successfully.")
"""

@login_required(login_url='login')
@admin_required
def administration(request):
    try:
        # Debug information
        print(f"User ID: {request.user.id}")
        print(f"Is Staff: {request.user.is_staff}")
        print(f"Is Admin: {hasattr(request.user, 'administrator')}")
        
        # Set is_staff flag if it's an administrator but not set as staff
        if hasattr(request.user, 'administrator') and not request.user.is_staff:
            print("Administrator found but is_staff is False. Setting is_staff to True.")
            request.user.is_staff = True
            request.user.save()
            
        user = User.objects.get(id = request.user.id)
        
        applications = Application.objects.all()
        registered_companies = Company.objects.all()
        jobs = Job.objects.all()
        shortlisted_applications = Application.objects.filter(status="accepted")
        
        # get the percentage of shortlisted students out of all students
        total_students = Application.objects.all().count()
        shortlisted_students = shortlisted_applications.count()
        
        if total_students > 0:
            shortlisted_percentage = (shortlisted_students / total_students) * 100
        else:
            shortlisted_percentage = 0    
        
        parameters = {
            "user": user,
            "applications": applications,
            "registered_companies": registered_companies,
            "jobs": jobs,
            "shortlisted_applications": shortlisted_applications,
            "shortlisted_percentage": int(shortlisted_percentage),
        }
        
        return render(request, "administration/index.html", parameters)
    except Exception as e:
        print(f"Error in administration view: {e}")
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('home')

# ============================================ COMPANIES =========================================

@login_required(login_url='login')
@admin_required
def companies(request):
    
    user = User.objects.get(id = request.user.id)
    
    companies = Company.objects.all()
    
    parameters = {
        "user": user,
        "companies": companies
    }
    
    return render(request, "administration/companies.html", parameters)


# ============================================ ALL REGISTRATIONS =========================================

@login_required(login_url='login')
@admin_required
def all_registrations(request):
        
    user = User.objects.get(id = request.user.id)
    
    applications = Application.objects.all()

    
    query = request.POST.get("query")
    print(query)
    if query:
        applications = applications.filter(
            Q(student__first_name__icontains=query) |
            Q(student__last_name__icontains=query) |
            Q(student__email__icontains=query) |
            Q(student__phone_number__icontains=query) |
            Q(student__year__icontains=query) |
            Q(job__company__name__icontains=query) |
            Q(status__icontains=query)
            
            )

    return render(request, "administration/all_registrations.html", {
        "user": user,
        "applications": applications,
        "query": query
    })

# ============================================ COMPANY =========================================

@login_required(login_url='login')
@admin_required
def company(request, id):
    user = User.objects.get(id=request.user.id)
    company = Company.objects.get(id=id)
    
    # Get all jobs for the company with their applications
    jobs = Job.objects.filter(company=company).prefetch_related('applications')
    
    # Calculate statistics
    total_applications = sum(job.applications.count() for job in jobs)
    
    # Calculate status counts
    pending_count = 0
    accepted_count = 0
    rejected_count = 0
    
    for job in jobs:
        for application in job.applications.all():
            if application.status == 'pending':
                pending_count += 1
            elif application.status == 'accepted':
                accepted_count += 1
            elif application.status == 'rejected':
                rejected_count += 1
    
    # Get job-wise statistics
    job_stats = []
    for job in jobs:
        job_applications = job.applications.all()
        job_stats.append({
            'title': job.title,
            'total': len(job_applications),
            'pending': sum(1 for a in job_applications if a.status == 'pending'),
            'accepted': sum(1 for a in job_applications if a.status == 'accepted'),
            'rejected': sum(1 for a in job_applications if a.status == 'rejected'),
        })
    
    parameters = {
        "user": user,
        "company": company,
        "jobs": jobs,
        "total_applications": total_applications,
        "pending_count": pending_count,
        "accepted_count": accepted_count,
        "rejected_count": rejected_count,
        "job_stats": job_stats,
    }
    
    return render(request, "administration/company.html", parameters)

# ============================================ JOB DETAILS ======================================

@login_required(login_url='login')
@admin_required
def job_details(request, slug):
    
    user = User.objects.get(id = request.user.id)
    job = Job.objects.get(slug=slug)
    
    parameters = {
        "user": user,
        "job": job,
    }
    
    return render(request, "administration/job_details.html", parameters)

# ============================================ APPLICATIONS =====================================

@login_required(login_url='login')
@admin_required
def applications(request, slug):
    
    user = User.objects.get(id = request.user.id)
    job = Job.objects.get(slug=slug)
    pending_applications = Application.objects.filter(job=job,status="pending")
    accepted_applications = Application.objects.filter(job=job,status="accepted")
    rejected_applications = Application.objects.filter(job=job,status="rejected")
     
    parameters = {
        "user": user,
        "job": job,
        "pending_applications": pending_applications,
        "accepted_applications": accepted_applications,
        "rejected_applications": rejected_applications
    }
    
    return render(request, "administration/applications.html", parameters)

# ============================================ MAIN PAGE SHORTLISTED STUDENTS =============================

@login_required(login_url='login')
@admin_required
def shortlisted_students(request):
    
    user = User.objects.get(id = request.user.id)
    shortlisted_applications = Application.objects.filter(status="accepted")
    
    query = request.GET.get("query")
    if query:
        shortlisted_applications = shortlisted_applications.filter(
            Q(student__first_name__icontains=query) |
            Q(student__last_name__icontains=query) |
            Q(student__email__icontains=query) |
            Q(student__phone_number__icontains=query) |
            Q(student__year__icontains=query))
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(shortlisted_applications, 20)  # Show 20 applications per page
    
    try:
        paginated_applications = paginator.page(page)
    except PageNotAnInteger:
        paginated_applications = paginator.page(1)
    except EmptyPage:
        paginated_applications = paginator.page(paginator.num_pages)

    return render(request, "administration/shortlisted_students.html", {
        "user": user,
        "shortlisted_applications": paginated_applications,
        "query": query,
        "total_count": shortlisted_applications.count()
    })

# ============================================ MAIN PAGE REJECTED STUDENTS =============================

@login_required(login_url='login')
@admin_required
def rejected_students(request):
    
    user = User.objects.get(id = request.user.id)
    rejected_applications = Application.objects.filter(status="rejected")
    
    query = request.GET.get("query")
    print(query)
    if query:
        rejected_applications = rejected_applications.filter(
            Q(student__first_name__icontains=query) |
            Q(student__last_name__icontains=query) |
            Q(student__email__icontains=query) |
            Q(student__phone_number__icontains=query) |
            Q(student__year__icontains=query))
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(rejected_applications, 20)  # Show 20 applications per page
    
    try:
        paginated_applications = paginator.page(page)
    except PageNotAnInteger:
        paginated_applications = paginator.page(1)
    except EmptyPage:
        paginated_applications = paginator.page(paginator.num_pages)

    return render(request, "administration/rejected_students.html", {
        "user": user,
        "rejected_applications": paginated_applications,
        "query": query,
        "total_count": rejected_applications.count()
    })

# ============================================ ADD NOTIFICATION =========================================

@login_required(login_url='login')
@admin_required
def add_notification(request):
    
    notifications = Notification.objects.all()[::-1]
    
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")

        notification = Notification(title=title, description=description)
        notification.save()
        
        all_mails = Student.objects.all().values_list('username', flat=True)
        all_mails = list(all_mails)
        
        # all_mails += [f"khandelwalprinci1+{i}@gmail.com" for i in range(100, 200)]
        # print(all_mails)

        # Comment out the external API email functions
        """
        thread = threading.Thread(target=send_emails_threaded, args=(all_mails, title, description))
        thread.start()
        """
        
        # Use Django's send_mail instead
        email_from = 'GLANCE JOB FAIR 2k24 <alumniassociation01@gla.ac.in>'
        
        # Send emails in batches to avoid timeout
        batch_size = 50
        for i in range(0, len(all_mails), batch_size):
            batch = all_mails[i:i+batch_size]
            try:
                send_mail(
                    title,
                    description,
                    email_from,
                    bcc=batch,  # Use BCC for privacy
                    fail_silently=False
                )
            except Exception as e:
                print(f"Error sending email batch {i//batch_size + 1}: {e}")
        
        # send_email_async(
        #             to=all_mails,
        #             subject=title,
        #             text=description
        #         )
        
        messages.success(request, "Notification added successfully.")
        
        return redirect("administration")
    
    parameters = {
        "notifications": notifications
    }
    
    return render(request, "administration/add_notification.html", parameters)

# =========================================== ALL STUDENTS ===========================================

@login_required(login_url='login')
@admin_required
def all_students(request):
    user = User.objects.get(id=request.user.id)
    
    # Use prefetch_related to reduce database queries
    # Note: Student inherits from User, so we don't need select_related('user')
    students_query = Student.objects.prefetch_related('application_set')
    
    # Get query parameter from both GET and POST for flexibility
    query = request.POST.get("query") or request.GET.get("query")
    
    # Apply database-level filtering if there's a query
    if query:
        students_query = students_query.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(username__icontains=query) |
            Q(phone_number__icontains=query) |
            Q(year__icontains=query) |
            Q(course__icontains=query)
        )
    
    # Annotate with application count to enable sorting at the database level
    students_query = students_query.annotate(application_count=Count('application'))
    
    # Sort by application count at the database level
    students_query = students_query.order_by('-application_count')
    
    # Get the total count
    total_count = students_query.count()
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(students_query, 50)  # Show 50 students per page for faster loading
    
    try:
        paginated_students = paginator.page(page)
    except PageNotAnInteger:
        paginated_students = paginator.page(1)
    except EmptyPage:
        paginated_students = paginator.page(paginator.num_pages)

    return render(request, "administration/all_students.html", {
        "user": user,
        "students": paginated_students,
        "query": query,
        "total_count": total_count
    })

# ===============================================================================================
# ======================================= APPLICATION STATUS CHANGE =============================
# ===============================================================================================

@login_required(login_url='login')
@admin_required
def accept_application(request, id):
    
    application = Application.objects.get(id=id)
    student = Student.objects.get(id=application.student.id)
    application.status = "accepted"

    myfile = f"""
Dear {student.first_name} {student.last_name},

Congratulations, {student.first_name}! You've been selected by {application.job.company.name.title()} for further consideration at the GLANCE Mega Job Fair, hosted by GLA University in collaboration with the Department of Alumni Affairs. 

Your dedication and impressive resume have caught the attention of {application.job.company.name.title()}. Prepare for the next steps as they're eager to move forward with you. Best of luck!

Here are the next steps in the process:

Interview Schedule: Your interview with {application.job.company.name.title()} is tentatively scheduled for {application.job.interview_date}. You can also check the student portal for updates.

Preparation: Research {application.job.company.name.title()} to understand their core values, products, and recent developments. Your enthusiasm for the opportunity will shine through during the interview.

Below are the essential details regarding the upcoming interview:

Interview Date: {application.job.interview_date}
Interview Mode: {application.job.interview_mode}
Job role: {application.job.role}
Job type: {application.job.job_type}

We have every confidence that you will represent yourself and GLA University admirably throughout this process. If you have any questions or need further assistance, please don't hesitate to reach out to us at alumniassociation01@gla.ac.in.

Once again, congratulations on your one step towards a fantastic accomplishment! We wish you the best of luck in your upcoming interview with {application.job.company.name.title()}.

Best regards,

Technical Team,
Department of Alumni Affairs,
GLA University, Mathura
"""

    email_subject = f"Subject: Congratulations! You've Been Selected by {application.job.company.name.title()} at GLANCE JOB FAIR 2k24"
    email_body = myfile
    email_from = 'GLANCE JOB FAIR 2k24 <alumniassociation01@gla.ac.in>'
    email_to = [student.username]

    # Send the email
    try:
        send_mail(
            email_subject, 
            email_body, 
            email_from, 
            email_to,
            fail_silently=False
            )
    except Exception as e:
        print(f"Error sending email: {e}")
        messages.warning(request, "Selection email will be sent to the student soon.")
    
    application.save()
    
    job = Job.objects.get(id=application.job.id)
    
    messages.success(request, "Application accepted successfully.")
    
    return redirect("applications", slug=job.slug)

# ================================== REJECT APPLICATION =========================================
        
@login_required(login_url='login')
@admin_required
def reject_application(request, id):
    
    application = Application.objects.get(id=id)
    student = Student.objects.get(id=application.student.id)
    application.status = "rejected"
    application.save()
    job = Job.objects.get(id=application.job.id)
    
    myfile = f"""
Dear {student.first_name} {student.last_name},

We hope this message finds you in good health and spirits.

We regret to inform you that your application for {job.company.name.title()} at GLANCE - the Mega Student Job Fair has not been successful. The selection process was highly competitive, and unfortunately, your application did not meet the specific criteria outlined by the participating companies.

While we understand that this news may be disappointing, don't loose hope. Please know that your participation and interest in GLANCE is highly valued. We encourage you to remain proactive in your job search and explore other opportunities available at the fair.

If you have any questions or require further assistance, please do not hesitate to reach out to us at alumniassociation01@gla.ac.in.

Thank you for your understanding, and we wish you the best of luck in your future endeavors.

Best regards,

Technical Team,
Department of Alumni Affairs,
GLA University, Mathura"""

    email_subject = f"Update on Your Application for GLANCE - Mega Student Job Fair"
    email_body = myfile
    email_from = 'GLANCE JOB FAIR 2k24 <alumniassociation01@gla.ac.in>'
    email_to = [student.username]

    # Send the email
    try:
        send_mail(
            email_subject, 
            email_body, 
            email_from, 
            email_to,
            fail_silently=False
            )
    except Exception as e:
        print(f"Error sending email: {e}")
        messages.warning(request, "Rejection email will be sent to the student soon.")
    
    
    messages.error(request, "Application rejected successfully.")
    
    return redirect("applications", slug=job.slug)

# ================================== CHANGE TO PENDING =========================================

@login_required(login_url='login')
@admin_required
def change_to_pending(request, id):
    
    application = Application.objects.get(id=id)
    application.status = "pending"
    application.save()
    
    job = Job.objects.get(id=application.job.id)
    
    messages.warning(request, "Application status changed to PENDING.")
    
    return redirect("applications", slug=job.slug)

# ===============================================================================================
# =========================================== COMPANY CHANGE ====================================
# ===============================================================================================

@login_required(login_url='login')
@admin_required
def add_company(request):
    
    if request.method == "POST":
        name = request.POST.get("name").title()
        description = request.POST.get("description").capitalize()
        location = request.POST.get("location")
        website = request.POST.get("website")
        size = request.POST.get("size")
        mail_id = request.POST.get("mail_id")
        logo = request.FILES.get("logo")
        
        company = Company(name=name,
                        location=location,
                        size=size,
                        mail_id=mail_id,
                        website=website,
                        description=description)
        
        if logo:
            company.logo = logo
        company.save()
        
        messages.success(request, "Company added successfully. Mail will be sent to students shortly")
        
        return redirect("companies")
    
    return render(request, "administration/add_company.html")

# ============================================ ADD JOB =========================================

@login_required(login_url='login')
@admin_required
def add_job(request, id):
    
    company = Company.objects.get(id=id)
    
    if request.method == "POST":
        title = request.POST.get("title").title()
        description = request.POST.get("description").capitalize()
        interview_date = request.POST.get("interview_date")
        deadline = request.POST.get("deadline")
        interview_mode = request.POST.get("interview_mode")
        tenth_percentage = request.POST.get("tenth_percentage")
        twelfth_percentage = request.POST.get("twelfth_percentage")
        cgpa = request.POST.get("cgpa")
        # is_backlog_allowed = request.POST.get("is_backlog_allowed")
        
        no_of_openings = request.POST.get("no_of_openings")
        job_type = request.POST.get("job_type")
        salary_range = request.POST.get("salary_range")
        location_flexibility = request.POST.get("location_flexibility")
        
        role = request.POST.get("role")
        
        job = Job(company=company,
                title=title,
                description=description,
                interview_date=interview_date,
                deadline=deadline,
                interview_mode=interview_mode,
                tenth_percentage=tenth_percentage,
                twelfth_percentage=twelfth_percentage,
                cgpa_criteria=cgpa,
                # is_backlog_allowed=is_backlog_allowed,
                no_of_openings=no_of_openings,
                job_type=job_type,
                salary_range=salary_range,
                location_flexibility=location_flexibility,
                role=role)
        
        job.save()
        
        messages.success(request, "Job added successfully.")
        
        return redirect("company", id=company.id)
    
    return render(request, "administration/add_job.html", {
        "company": company
    })
    
# =======

import csv
from django.http import HttpResponse
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

# ====================

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

# ====================

def export_company_applications_summary_csv(request):
    # Get all companies with the total number of applications for each company
    companies_with_applications_count = Company.objects.annotate(total_applications=Count('jobs__applications'))

    # Define the CSV file response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="company_applications_summary.csv"'

    # Create a CSV writer
    writer = csv.writer(response)

    # Write the header row
    writer.writerow(['Company Name', 'Total Applications'])

    # Write data rows
    for company in companies_with_applications_count:
        writer.writerow([company.name, company.total_applications])

    return response


# ==============================

# This code was causing migration errors because it runs at import time
# It should be moved to a management command or a view function

# for student in Student.objects.all():
#     student.no_of_companies_left = 10
#     student.save()

@login_required(login_url='login')
@admin_required
def filter_page(request):
    """
    View for the advanced filter page with DataTables integration
    """
    user = User.objects.get(id=request.user.id)
    
    # Get all companies and jobs for dropdowns
    companies = Company.objects.all().order_by('name')
    jobs = Job.objects.all().order_by('title')
    
    return render(request, "administration/filter_page.html", {
        "user": user,
        "companies": companies,
        "jobs": jobs,
    })

@login_required(login_url='login')
@admin_required
def get_filtered_students(request):
    """
    AJAX view to handle filtering students based on various criteria
    """
    import json
    import traceback
    
    # Debug output at the start
    print("="*50)
    print("get_filtered_students called")
    print("="*50)
    
    try:
        # Get all students first to check if database has data
        all_students = Student.objects.all()
        total_students = all_students.count()
        print(f"Total students in database: {total_students}")
        
        # If no students in database, return empty response
        if total_students == 0:
            print("No students found in database!")
            return JsonResponse({
                'draw': int(request.GET.get('draw', 1)),
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'data': [],
                'message': 'No students found in database'
            })
            
        # Start with all students for filtering
        students = all_students
        print(f"Initial student count: {students.count()}")
        
        # Get DrawTable parameters - these are sent by DataTables
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 25))
        
        # Print all request parameters for debugging
        print("Request GET parameters:")
        for key, value in request.GET.items():
            print(f"  {key}: {value}")
        
        # Basic filters
        student_id = request.GET.get('id')
        name = request.GET.get('name')
        email = request.GET.get('email')
        phone = request.GET.get('phone')
        
        # Course filter (multiple selection)
        courses = request.GET.getlist('course[]') or request.GET.getlist('course')
        print(f"Courses from request: {courses}")
        
        # Company and job filters (from both dropdowns and checkbox groups)
        company_ids = request.GET.getlist('companies[]') or request.GET.getlist('companies')
        job_ids = request.GET.getlist('jobs[]') or request.GET.getlist('jobs')
        
        # Interview date filter (multiple selection)
        interview_dates = request.GET.getlist('interview_date[]') or request.GET.getlist('interview_date')
        
        # For backward compatibility
        company = request.GET.get('company')
        job = request.GET.get('job')
        
        print(f"Company IDs: {company_ids}")
        print(f"Job IDs: {job_ids}")
        print(f"Interview dates: {interview_dates}")
        
        # Other filters
        year = request.GET.get('year')
        cgpa = request.GET.get('cgpa')
        cgpa_operator = request.GET.get('cgpa_operator', '=')
        status = request.GET.get('status')
        companies_left = request.GET.get('companies_left')
        companies_operator = request.GET.get('companies_operator', '=')
        profile_score = request.GET.get('profile_score')
        score_operator = request.GET.get('score_operator', '=')
        attendance_status = request.GET.get('attendance_status')
        
        # Apply basic filters
        if student_id:
            students = students.filter(id=student_id)
            print(f"After ID filter: {students.count()} students")
        if name:
            students = students.filter(Q(first_name__icontains=name) | Q(last_name__icontains=name))
            print(f"After name filter: {students.count()} students")
        if email:
            students = students.filter(email__icontains=email)
            print(f"After email filter: {students.count()} students")
        if phone:
            students = students.filter(phone_number__icontains=phone)
            print(f"After phone filter: {students.count()} students")
        
        # Apply course filter
        if courses:
            print(f"Filtering by courses: {courses}")
            students = students.filter(course__in=courses)
            print(f"After course filter: {students.count()} students")
        
        # Apply company filter using company IDs
        if company_ids:
            print(f"Filtering by company IDs: {company_ids}")
            try:
                # Get applications for the specified companies
                company_applications = Application.objects.filter(
                    job__company__id__in=company_ids
                ).values_list('student_id', flat=True).distinct()
                
                students = students.filter(id__in=company_applications)
                print(f"After company ID filter: {students.count()} students")
            except Exception as e:
                print(f"Error filtering by company IDs: {e}")
        # Apply old company filter for backward compatibility
        elif company:
            print(f"Filtering by company name: {company}")
            try:
                # Get applications for the specified company
                company_applications = Application.objects.filter(
                    job__company__name=company
                ).values_list('student_id', flat=True).distinct()
                
                students = students.filter(id__in=company_applications)
                print(f"After company name filter: {students.count()} students")
            except Exception as e:
                print(f"Error filtering by company name: {e}")
        
        # Apply job filter using job IDs
        if job_ids:
            print(f"Filtering by job IDs: {job_ids}")
            try:
                # Get applications for the specified jobs
                job_applications = Application.objects.filter(
                    job__id__in=job_ids
                ).values_list('student_id', flat=True).distinct()
                
                students = students.filter(id__in=job_applications)
                print(f"After job ID filter: {students.count()} students")
            except Exception as e:
                print(f"Error filtering by job IDs: {e}")
        # Apply old job filter for backward compatibility
        elif job:
            print(f"Filtering by job title: {job}")
            try:
                # Get applications for the specified job
                job_applications = Application.objects.filter(
                    job__title=job
                ).values_list('student_id', flat=True).distinct()
                
                students = students.filter(id__in=job_applications)
                print(f"After job title filter: {students.count()} students")
            except Exception as e:
                print(f"Error filtering by job title: {e}")
        
        # Apply interview date filter
        if interview_dates:
            print(f"Filtering by interview dates: {interview_dates}")
            try:
                # Get students with applications for jobs with these interview dates
                students = students.filter(
                    application__job__interview_date__in=interview_dates
                ).distinct()
                print(f"After interview date filter: {students.count()} students")
            except Exception as e:
                print(f"Error filtering by interview dates: {e}")
        
        # Apply year filter
        if year:
            students = students.filter(year=year)
            print(f"After year filter: {students.count()} students")
        
        # Apply CGPA filter
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
                print(f"After CGPA filter: {students.count()} students")
            except (ValueError, TypeError):
                print("Invalid CGPA value:", cgpa)
        
        # Apply status filter
        if status:
            students = students.filter(alumni_status=status)
            print(f"After status filter: {students.count()} students")
        
        # Apply companies left filter
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
                print(f"After companies left filter: {students.count()} students")
            except (ValueError, TypeError):
                print("Invalid companies left value:", companies_left)
        
        # Apply profile score filter
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
                print(f"After profile score filter: {students.count()} students")
            except (ValueError, TypeError) as e:
                print(f"Error filtering by profile score: {e}")
                pass
        
        # Apply attendance status filter
        if attendance_status:
            print(f"Filtering by attendance status: {attendance_status}")
            if attendance_status == 'present':
                # Find students who have attendances marked as present
                students = students.filter(attendance__is_present=True).distinct()
            elif attendance_status == 'absent':
                # Find students who have attendances marked as absent
                students = students.filter(attendance__is_present=False).distinct()
            elif attendance_status == 'not_marked':
                # This is more complex - we need to find students with no attendance records
                students_with_attendance = Attendance.objects.values_list('student_id', flat=True).distinct()
                students = students.exclude(id__in=students_with_attendance)
            print(f"After attendance filter: {students.count()} students")
                
        # Count total filtered records before pagination
        total_filtered_records = students.count()
        print(f"Total filtered records: {total_filtered_records}")
        
        # Apply pagination
        paginated_students = students[start:start + length]
        print(f"After pagination: {len(paginated_students)} students")
        
        # Convert student data to format expected by DataTables
        data = []
        for student in paginated_students:
            try:
                # Handle profile score calculation
                try:
                    profile_score_val = 75  # Default profile score
                    if hasattr(student, 'get_profile_score'):
                        student_score = student.get_profile_score()
                        if student_score is not None:
                            profile_score_val = student_score
                except Exception as e:
                    print(f"Error getting profile score for student {student.id}: {e}")
                    profile_score_val = 0
                
                # Formatted student data for DataTables
                data.append({
                    'id': student.id,
                    'name': f"{student.first_name or ''} {student.last_name or ''}".strip(),
                    'email': student.email or '',
                    'phone': student.phone_number or '',
                    'course': student.course or '',
                    'year': student.year or '',
                    'cgpa': float(student.cgpa) if student.cgpa else 0,
                    'status': student.alumni_status or 'Active',
                    'companies_left': student.no_of_companies_left or 0,
                    'profile_score': profile_score_val,
                    'actions': f'<a href="/administration/student/{student.id}" class="btn btn-sm btn-primary"><i class="fas fa-eye"></i></a>'
                })
            except Exception as e:
                print(f"Error processing student {getattr(student, 'id', 'unknown')}: {e}")
                continue
        
        # Create response for DataTables
        response = {
            'draw': draw,
            'recordsTotal': total_students,
            'recordsFiltered': total_filtered_records,
            'data': data
        }
        
        print(f"Returning {len(data)} students to DataTable")
        return JsonResponse(response)
    
    except Exception as e:
        import traceback
        print(f"Error in get_filtered_students: {e}")
        print(traceback.format_exc())
        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': str(e)
        })

@login_required(login_url='login')
@admin_required
def send_message_to_filtered_students(request):
    """Send messages to filtered students with both email and notification"""
    if request.method == "POST":
        # Extract the message details
        subject = request.POST.get("subject")
        content = request.POST.get("content")
        
        # Get filter parameters from request
        id = request.POST.get('id', '')
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        courses = request.POST.getlist('course')  # Get all selected courses
        year = request.POST.get('year', '')
        cgpa = request.POST.get('cgpa', '')
        cgpa_operator = request.POST.get('cgpa_operator', '=')
        status = request.POST.get('status', '')
        companies_left = request.POST.get('companies_left', '')
        companies_operator = request.POST.get('companies_operator', '=')
        profile_score = request.POST.get('profile_score', '')
        score_operator = request.POST.get('score_operator', '=')
        company = request.POST.get('company', '')
        job = request.POST.get('job', '')
        attendance_status = request.POST.get('attendance_status', '')
        
        # Debug output
        print(f"Message filter params: id={id}, name={name}, email={email}, phone={phone}, courses={courses}, year={year}")
        print(f"Advanced filter params: cgpa={cgpa}({cgpa_operator}), status={status}, companies_left={companies_left}({companies_operator})")
        print(f"Additional filters: profile_score={profile_score}({score_operator}), company='{company}', job='{job}', attendance='{attendance_status}'")
        
        # Start with all students
        students = Student.objects.all()
        total_students = students.count()
        print(f"Starting with {total_students} total students")
        
        # Apply filters
        if id:
            students = students.filter(id__icontains=id)
            print(f"After ID filter: {students.count()} students")
        if name:
            students = students.filter(Q(first_name__icontains=name) | Q(last_name__icontains=name))
            print(f"After name filter: {students.count()} students")
        if email:
            students = students.filter(username__icontains=email)
            print(f"After email filter: {students.count()} students")
        if phone:
            students = students.filter(phone_number__icontains=phone)
            print(f"After phone filter: {students.count()} students")
        if courses:
            # Filter students who have any of the selected courses
            course_query = Q()
            for course in courses:
                course_query |= Q(course__icontains=course)
            students = students.filter(course_query)
            print(f"After course filter: {students.count()} students")
        if year and year != 'all':
            students = students.filter(year=year)
            print(f"After year filter: {students.count()} students")
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
                print(f"After CGPA filter: {students.count()} students")
            except (ValueError, TypeError) as e:
                print(f"Error applying CGPA filter: {e}")
                pass
        if status:
            students = students.filter(alumni_status=status)
            print(f"After status filter: {students.count()} students")
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
                print(f"After companies left filter: {students.count()} students")
            except (ValueError, TypeError) as e:
                print(f"Error applying companies left filter: {e}")
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
                print(f"After profile score filter: {students.count()} students")
            except (ValueError, TypeError) as e:
                print(f"Error filtering by profile score: {e}")
                pass
                
        # Filter by company and job applications if provided
        if company:
            # Get applications for the specified company
            company_applications = Application.objects.filter(
                job__company__name__icontains=company
            ).values_list('student_id', flat=True)
            students = students.filter(id__in=company_applications)
            print(f"After company filter: {students.count()} students")
            
        if job:
            # Get applications for the specified job
            job_applications = Application.objects.filter(
                job__title__icontains=job
            ).values_list('student_id', flat=True)
            students = students.filter(id__in=job_applications)
            print(f"After job filter: {students.count()} students")
        
        # Filter by attendance status if provided
        if attendance_status:
            if attendance_status == 'present':
                # Get student IDs who are marked present
                present_students = Application.objects.filter(
                    attendance__is_present=True
                ).values_list('student_id', flat=True).distinct()
                students = students.filter(id__in=present_students)
                print(f"After attendance (present) filter: {students.count()} students")
            elif attendance_status == 'absent':
                # Get student IDs who are marked absent
                absent_students = Application.objects.filter(
                    attendance__is_present=False
                ).values_list('student_id', flat=True).distinct()
                students = students.filter(id__in=absent_students)
                print(f"After attendance (absent) filter: {students.count()} students")
            elif attendance_status == 'not_marked':
                # Get student IDs who have applications but no attendance record
                application_student_ids = Application.objects.values_list('student_id', flat=True).distinct()
                attendance_student_ids = Application.objects.filter(
                    attendance__isnull=False
                ).values_list('student_id', flat=True).distinct()
                not_marked_student_ids = set(application_student_ids) - set(attendance_student_ids)
                students = students.filter(id__in=not_marked_student_ids)
                print(f"After attendance (not marked) filter: {students.count()} students")
        
        # Get all student emails
        student_emails = students.values_list('username', flat=True)
        student_emails = list(student_emails)
        
        # 1. Create and save a notification
        notification = Notification(title=subject, description=content)
        notification.save()
        
        # 2. Send emails to all filtered students
        if student_emails:
            email_from = 'GLANCE JOB FAIR 2k24 <alumniassociation01@gla.ac.in>'
            
            # Send emails in batches to avoid timeout
            batch_size = 50
            for i in range(0, len(student_emails), batch_size):
                batch = student_emails[i:i+batch_size]
                try:
                    send_mail(
                        subject,
                        content,
                        email_from,
                        bcc=batch,  # Use BCC for privacy
                        fail_silently=False
                    )
                    print(f"Successfully sent email batch {i//batch_size + 1} of {len(student_emails)//batch_size + 1}")
                except Exception as e:
                    print(f"Error sending email batch {i//batch_size + 1}: {e}")
            
            messages.success(request, f"Message sent successfully to {len(student_emails)} students.")
        else:
            messages.warning(request, "No students match the specified filters.")
        
        return redirect("filter_page")
    
    # If not POST, redirect back to filter page
    return redirect("filter_page")

@login_required(login_url='login')
@admin_required
def whatsapp_message(request):
    """Render the WhatsApp messaging page"""
    return render(request, 'administration/whatsapp_message.html')

@login_required(login_url='login')
@admin_required
def whatsapp_test(request):
    """Render the WhatsApp test page"""
    return render(request, 'administration/whatsapp_test.html')

@login_required(login_url='login')
@admin_required
def send_whatsapp_to_filtered_students(request):
    """Generate WhatsApp message links for filtered students or a single recipient"""
    if request.method == "POST":
        # Extract the message content
        content = request.POST.get("content")
        export_mode = request.POST.get("export_mode", "urls")  # 'urls' or 'csv'
        
        # Check if this is a simple direct message to one recipient
        recipient = request.POST.get('recipient')
        if recipient:
            # Handle single recipient case
            try:
                # Format phone number for WhatsApp
                phone_number = recipient.strip()
                if not phone_number.startswith('+'):
                    if len(phone_number) == 10:
                        phone_number = '+91' + phone_number  # Default to India country code
                
                # Create WhatsApp URL
                whatsapp_url = f"https://wa.me/{phone_number.replace('+', '')}?text={content}"
                
                # Create a notification record
                notification = Notification(
                    title="WhatsApp Message Sent",
                    description=f"WhatsApp message sent to {phone_number}"
                )
                notification.save()
                
                # Redirect to WhatsApp URL
                return redirect(whatsapp_url)
            except Exception as e:
                messages.error(request, f"Error generating WhatsApp URL: {str(e)}")
                return redirect("whatsapp_message")
        
        # Continue with the original multiple recipient case
        # Get filter parameters from request
        id = request.POST.get('id', '')
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        courses = request.POST.getlist('course')  # Get all selected courses
        year = request.POST.get('year', '')
        attendance_status = request.POST.get('attendance_status', '')
        company = request.POST.get('company', '')
        
        # Debug output
        print(f"WhatsApp filter params: id={id}, name={name}, email={email}, phone={phone}")
        print(f"Other filters: courses={courses}, year={year}, attendance_status={attendance_status}, company={company}")
        
        # Start with all students
        students = Student.objects.all()
        total_students = students.count()
        print(f"Starting with {total_students} total students")
        
        # Apply filters
        if id:
            students = students.filter(id__icontains=id)
            print(f"After ID filter: {students.count()} students")
        if name:
            students = students.filter(Q(first_name__icontains=name) | Q(last_name__icontains=name))
            print(f"After name filter: {students.count()} students")
        if email:
            students = students.filter(username__icontains=email)
            print(f"After email filter: {students.count()} students")
        if phone:
            students = students.filter(phone_number__icontains=phone)
            print(f"After phone filter: {students.count()} students")
        if courses:
            # Filter students who have any of the selected courses
            course_query = Q()
            for course in courses:
                course_query |= Q(course__icontains=course)
            students = students.filter(course_query)
            print(f"After course filter: {students.count()} students")
        if year and year != 'all':
            students = students.filter(year=year)
            print(f"After year filter: {students.count()} students")
        
        # Filter by company applications if provided
        if company:
            # Get applications for the specified company
            company_applications = Application.objects.filter(
                job__company__name__icontains=company
            ).values_list('student_id', flat=True)
            students = students.filter(id__in=company_applications)
            print(f"After company filter: {students.count()} students")
        
        # Filter by attendance status if provided
        if attendance_status:
            if attendance_status == 'present':
                # Get student IDs who are marked present
                present_students = Application.objects.filter(
                    attendance__is_present=True
                ).values_list('student_id', flat=True).distinct()
                students = students.filter(id__in=present_students)
                print(f"After attendance (present) filter: {students.count()} students")
            elif attendance_status == 'absent':
                # Get student IDs who are marked absent
                absent_students = Application.objects.filter(
                    attendance__is_present=False
                ).values_list('student_id', flat=True).distinct()
                students = students.filter(id__in=absent_students)
                print(f"After attendance (absent) filter: {students.count()} students")
            elif attendance_status == 'not_marked':
                # Get student IDs who have applications but no attendance record
                application_student_ids = Application.objects.values_list('student_id', flat=True).distinct()
                attendance_student_ids = Application.objects.filter(
                    attendance__isnull=False
                ).values_list('student_id', flat=True).distinct()
                not_marked_student_ids = set(application_student_ids) - set(attendance_student_ids)
                students = students.filter(id__in=not_marked_student_ids)
                print(f"After attendance (not marked) filter: {students.count()} students")
        
        # Filter for students with phone numbers only
        students = students.exclude(phone_number__isnull=True).exclude(phone_number='')
        print(f"After filtering for valid phone numbers: {students.count()} students")
        
        # CSV export mode
        if export_mode == 'csv':
            import csv
            from django.http import HttpResponse
            from datetime import datetime
            
            response = HttpResponse(content_type='text/csv')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f'whatsapp_recipients_{timestamp}.csv'
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            writer = csv.writer(response)
            writer.writerow(['id', 'name', 'phone', 'email', 'course', 'year'])
            
            for student in students:
                writer.writerow([
                    student.id,
                    f"{student.first_name} {student.last_name}",
                    student.phone_number,
                    student.username,
                    student.course,
                    student.year
                ])
            
            # Create a notification record
            notification = Notification(
                title="WhatsApp Recipients Export",
                description=f"Exported {students.count()} students for WhatsApp messaging with filter: {name or 'all students'}"
            )
            notification.save()
            
            return response
        
        # Default URL generation mode
        else:
            # Create WhatsApp message URLs for each student
            whatsapp_data = []
            valid_count = 0
            
            for student in students:
                try:
                    # Format phone number for WhatsApp
                    phone_number = student.phone_number.strip()
                    phone_number = ''.join(filter(str.isdigit, phone_number))
                    
                    # Add country code if missing
                    if not phone_number.startswith('+'):
                        if len(phone_number) == 10:
                            phone_number = '+91' + phone_number  # Default to India country code
                        elif phone_number.startswith('91') and len(phone_number) == 12:
                            phone_number = '+' + phone_number
                    elif phone_number.startswith('+'):
                        phone_number = phone_number[1:]  # Remove + for URL
                    
                    # Skip if phone number is invalid
                    if len(phone_number) < 10:
                        continue
                    
                    # Personalize message content
                    personalized_content = content
                    personalized_content = personalized_content.replace(
                        '{{name}}', f"{student.first_name} {student.last_name}"
                    )
                    personalized_content = personalized_content.replace(
                        '{{company}}', company or "the company"
                    )
                    
                    # Create WhatsApp URL
                    whatsapp_url = f"https://wa.me/{phone_number}?text={personalized_content}"
                    
                    whatsapp_data.append({
                        'id': student.id,
                        'name': f"{student.first_name} {student.last_name}",
                        'phone': phone_number,
                        'message': personalized_content,
                        'url': whatsapp_url
                    })
                    
                    valid_count += 1
                except Exception as e:
                    print(f"Error creating WhatsApp URL for student {student.id}: {e}")
            
            # Create a notification record
            notification = Notification(
                title="WhatsApp Message Campaign",
                description=f"WhatsApp campaign with message: {content[:50]}..." if len(content) > 50 else content
            )
            notification.save()
            
            return JsonResponse({
                'success': True,
                'total_students': students.count(),
                'sent_count': valid_count,
                'whatsapp_data': whatsapp_data[:20],  # Only return first 20 to avoid large responses
                'automation_command': f"python manage.py send_whatsapp_bulk --message \"{content}\" --filter-json '{{\"name\":\"{name}\",\"course\":\"{course}\",\"attendance_status\":\"{attendance_status}\",\"company\":\"{company}\"}}'"
            })
    
    # If not POST, redirect back to WhatsApp page
    return redirect("whatsapp_message")

@login_required(login_url='login')
@admin_required
def send_whatsapp_bulk_csv(request):
    """Handle CSV upload for bulk WhatsApp messaging"""
    if request.method == "POST":
        # Get form data
        csv_file = request.FILES.get('csv_file')
        message_template = request.POST.get('bulk_message')
        delay_min = int(request.POST.get('delay_min', 10))
        delay_max = int(request.POST.get('delay_max', 30))
        limit = request.POST.get('limit')
        test_mode = request.POST.get('test_mode') == 'on'
        
        # Validate inputs
        if not csv_file or not message_template:
            messages.error(request, "CSV file and message template are required")
            return redirect('whatsapp_message')
        
        # Save the uploaded CSV file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
            for chunk in csv_file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name
        
        try:
            # Create a notification record
            notification = Notification(
                title="WhatsApp Bulk Messaging",
                description=f"Bulk WhatsApp messaging initiated with CSV file: {csv_file.name}"
            )
            notification.save()
            
            # Prepare command arguments
            cmd_args = [
                "python", "manage.py", "send_whatsapp_bulk",
                f"--message", f'"{message_template}"',
                f"--csv", f'"{temp_file_path}"',
                f"--delay-min", str(delay_min),
                f"--delay-max", str(delay_max)
            ]
            
            if limit:
                cmd_args.extend(["--limit", str(limit)])
            
            if test_mode:
                cmd_args.append("--test-mode")
            
            # Execute the command
            import subprocess
            
            # For test mode, just show the command that would be executed
            if test_mode:
                cmd_str = " ".join(cmd_args)
                messages.info(request, f"Test mode: Command that would be executed: {cmd_str}")
                
                # Show preview of CSV data
                import pandas as pd
                try:
                    df = pd.read_csv(temp_file_path)
                    preview_html = df.head(5).to_html(classes='table table-striped', index=False)
                    messages.info(request, f"CSV Preview (first 5 rows): {preview_html}")
                except Exception as e:
                    messages.error(request, f"Error reading CSV file: {str(e)}")
            else:
                # Execute the command
                process = subprocess.Popen(
                    cmd_args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                stdout, stderr = process.communicate()
                
                if process.returncode == 0:
                    messages.success(request, "Bulk WhatsApp messaging initiated successfully")
                    messages.info(request, f"Command output: {stdout}")
                else:
                    messages.error(request, f"Error executing command: {stderr}")
            
            # Clean up the temporary file
            os.unlink(temp_file_path)
            
        except Exception as e:
            messages.error(request, f"Error processing CSV file: {str(e)}")
            # Clean up the temporary file in case of error
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
        return redirect('whatsapp_message')
    
    # If not POST, redirect to the WhatsApp message page
    return redirect('whatsapp_message')

@login_required(login_url='login')
@admin_required
def download_whatsapp_csv_template(request):
    """Generate and download a sample CSV template for WhatsApp bulk messaging"""
    import csv
    from django.http import HttpResponse
    
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="whatsapp_recipients_template.csv"'
    
    # Create CSV writer
    writer = csv.writer(response)
    
    # Write header row
    writer.writerow(['phone', 'name'])
    
    # Write sample data rows
    writer.writerow(['+919876543210', 'John Doe'])
    writer.writerow(['+919876543211', 'Jane Smith'])
    writer.writerow(['+919876543212', 'Robert Johnson'])
    
    return response

@login_required(login_url='login')
@admin_required
def test_student_data(request):
    """
    Simple test view to return student data as JSON
    Used to verify data access is working correctly
    """
    try:
        students = Student.objects.all()
        
        # Debug output
        print(f"test_student_data: Found {students.count()} students")
        for student in students:
            print(f"Student: {student.id} - {student.first_name} {student.last_name} - {student.email}")
        
        data = []
        for student in students:
            data.append({
                'id': student.id,
                'name': f"{student.first_name} {student.last_name}",
                'email': student.email,
                'phone': student.phone_number,
                'course': student.course,
                'cgpa': student.cgpa
            })
        
        return JsonResponse({
            'success': True,
            'count': len(data),
            'data': data
        })
    except Exception as e:
        import traceback
        print("Error in test_student_data:", str(e))
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required(login_url='login')
@admin_required
def get_all_students_json(request):
    """API endpoint to get all students as JSON for DataTables"""
    try:
        students = Student.objects.all()
        
        print(f"Found {students.count()} students for JSON response")
        
        data = []
        for student in students:
            # Handle profile score
            try:
                profile_score = 75  # Default profile score
                if hasattr(student, 'get_profile_score'):
                    student_score = student.get_profile_score()
                    if student_score is not None:
                        profile_score = student_score
            except Exception as e:
                print(f"Error getting profile score for student {student.id}: {e}")
                profile_score = 0
                
            # Create a data entry for this student
            data.append({
                'id': student.id,
                'name': f"{student.first_name or ''} {student.last_name or ''}".strip(),
                'email': student.email or '',
                'phone': student.phone_number or '',
                'course': student.course or '',
                'year': student.year or '',
                'cgpa': float(student.cgpa) if student.cgpa else 0,
                'status': student.alumni_status or 'Active',
                'companies_left': student.no_of_companies_left or 0,
                'profile_score': profile_score,
                'actions': f'<a href="/administration/student/{student.id}" class="btn btn-sm btn-primary"><i class="fas fa-eye"></i></a>'
            })
            
        return JsonResponse({
            'data': data
        })
    except Exception as e:
        import traceback
        print(f"Error in get_all_students_json: {e}")
        print(traceback.format_exc())
        return JsonResponse({
            'error': str(e),
            'data': []
        })

@login_required(login_url='login')
@admin_required
def update_company_limit(request):
    """Update company limit for students"""
    if request.method == 'POST':
        limit = int(request.POST.get('limit', 10))
        filter_type = request.POST.get('filter', 'all')
        
        # Check if we're working with selected students
        student_ids = request.POST.getlist('student_ids')
        if filter_type == 'selected' and student_ids:
            # Update only the selected students
            queryset = Student.objects.filter(id__in=student_ids)
        else:
            # Apply filter
            if filter_type == 'less_than_limit':
                queryset = Student.objects.filter(no_of_companies_left__lt=limit)
            elif filter_type == 'zero':
                queryset = Student.objects.filter(no_of_companies_left=0)
            else:  # 'all'
                queryset = Student.objects.all()
        
        # Update the limit
        students_updated = queryset.update(no_of_companies_left=limit)
        
        # Show success message
        if students_updated == 0:
            messages.warning(request, f"No students were updated")
        else:
            messages.success(request, f"Successfully updated {students_updated} students to have {limit} company limit")
        
        # Redirect back to referring page or a default
        return redirect(request.META.get('HTTP_REFERER', 'all_students'))
    
    # If GET request, just redirect to all students page
    return redirect('all_students')

@login_required(login_url='login')
@admin_required
def bypass_cgpa_validation(request):
    """Toggle bypass_eligibility flag for students"""
    if request.method == 'POST':
        action = request.POST.get('action', 'enable')
        
        # Get filter type
        filter_type = request.POST.get('filter', 'all')
        
        # Check if we're working with selected students
        student_ids = request.POST.getlist('student_ids')
        if filter_type == 'selected' and student_ids:
            # Update only the selected students
            queryset = Student.objects.filter(id__in=student_ids)
        else:
            # Apply filter for all students
            queryset = Student.objects.all()
        
        # Update the bypass_eligibility flag
        if action == 'enable':
            students_updated = queryset.update(bypass_eligibility=True)
            message = f"Successfully enabled CGPA bypass for {students_updated} students"
        else:
            students_updated = queryset.update(bypass_eligibility=False)
            message = f"Successfully disabled CGPA bypass for {students_updated} students"
        
        if students_updated == 0:
            messages.warning(request, "No students were updated")
        else:
            messages.success(request, message)
        
        # Redirect back to referring page or a default
        return redirect(request.META.get('HTTP_REFERER', 'all_students'))
    
    # If GET request, just redirect to all students page
    return redirect('all_students')