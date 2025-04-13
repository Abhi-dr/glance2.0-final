from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from accounts.models import Company, Job, Student, Application, Notification
from django.db.models import Q

import threading

from django.core.mail import send_mail

import requests

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
@staff_member_required(login_url='login')
def administration(request):
    
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

# ============================================ COMPANIES =========================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
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
@staff_member_required(login_url='login')
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
@staff_member_required(login_url='login')
def company(request, id):
    
    user = User.objects.get(id = request.user.id)
    
    company = Company.objects.get(id=id)
    jobs = Job.objects.filter(company=company)
    
    
    parameters = {
        "user": user,
        "company": company,
        "jobs": jobs
    }
    
    return render(request, "administration/company.html", parameters)

# ============================================ JOB DETAILS ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
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
@staff_member_required(login_url='login')
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
@staff_member_required(login_url='login')
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

    return render(request, "administration/shortlisted_students.html", {
        "user": user,
        "shortlisted_applications": shortlisted_applications,
        "query": query
    })

# ============================================ MAIN PAGE REJECTED STUDENTS =============================

@login_required(login_url='login')
@staff_member_required(login_url='login')
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

    return render(request, "administration/rejected_students.html", {
        "user": user,
        "rejected_applications": rejected_applications,
        "query": query
    })

# ============================================ ADD NOTIFICATION =========================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
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
@staff_member_required(login_url='login')
def all_students(request):
        
    user = User.objects.get(id = request.user.id)
    students = Student.objects.all()
    
    # sort the students based on the number of jobs they have applied for
    
    students = sorted(students, key=lambda x: x.application_set.count(), reverse=True)
    
    query = request.POST.get("query")
    if query:
        students = students.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone_number__icontains=query) |
            Q(year__icontains=query) |
            Q(course__icontains=query))
        
        

    return render(request, "administration/all_students.html", {
        "user": user,
        "students": students,
        "query": query
    })

# ===============================================================================================
# ======================================= APPLICATION STATUS CHANGE =============================
# ===============================================================================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
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
@staff_member_required(login_url='login')
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
@staff_member_required(login_url='login')
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
@staff_member_required(login_url='login')
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
@staff_member_required(login_url='login')
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