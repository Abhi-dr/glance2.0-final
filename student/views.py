from django.shortcuts import render, redirect
from accounts.models import Student, Company, Job, Application, Notification
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from datetime import datetime
from django.db.models import Q
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

# ========================================= DASHBOARD =========================================


@login_required(login_url='login')
def home(request):
    
    student = Student.objects.get(id=request.user.id)

    # Initialize variables with default values
    no_of_companies_applied = 0
    eligible_jobs = []
    all_eligible_jobs = []
    eligible_companies_count = 0
    applications = []
    
    # Get application count safely
    no_of_companies_applied = Application.objects.filter(student=student).count()
    no_of_companies_applied_in_percentage = min(no_of_companies_applied * 50, 100)  # Cap at 100%
    
    # Get total companies count safely
    companies_count = Job.objects.all().count() or 1  # Avoid division by zero
    
    # Check if student has complete profile
    has_complete_profile = all([
        student.tenth is not None,
        student.twelfth is not None,
        student.cgpa is not None
    ])
    
    if has_complete_profile:
        # Get eligible jobs with proper error handling
        try:
            # Base query for eligible jobs
            all_eligible_jobs = Job.objects.filter(
                tenth_percentage__lte=student.tenth,
                twelfth_percentage__lte=student.twelfth,
                cgpa_criteria__lte=student.cgpa,
            ).exclude(applications__student=student)
            
            # Handle backlog restrictions
            if student.backlog > 0:
                all_eligible_jobs = all_eligible_jobs.exclude(is_backlog_allowed=False)
            
            # Get applications to handle interview date conflicts
            applications = Application.objects.filter(student=student)
            
            # Exclude jobs with interview date conflicts
            for application in applications:
                if application.job and application.job.interview_date:
                    all_eligible_jobs = all_eligible_jobs.exclude(
                        interview_date=application.job.interview_date
                    )
            
            # Calculate percentage of eligible companies
            eligible_companies_count = int((all_eligible_jobs.count() / companies_count) * 100)
            
            # Create duplicate for displaying limited results
            eligible_jobs = all_eligible_jobs[:3]  # First 3 jobs for dashboard

        except Exception as e:
            # Log the exception for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in home view: {str(e)}")
            
            # Set empty queryset
            all_eligible_jobs = Job.objects.none()
            eligible_jobs = Job.objects.none()
            eligible_companies_count = 0
    else:
        messages.info(request, "Complete your profile to see eligible jobs for you 🔥")
        all_eligible_jobs = Job.objects.none()
        eligible_jobs = Job.objects.none()
    
    parameters = {
        "student": student,
        "no_of_companies_applied": no_of_companies_applied,
        "eligible_jobs": eligible_jobs,
        "all_eligible_jobs": all_eligible_jobs,
        "no_of_companies_applied_in_percentage": no_of_companies_applied_in_percentage,
        "eligible_companies_count": eligible_companies_count,
        "applications": applications,
        "has_complete_profile": has_complete_profile
    }
    
    return render(request, "student/index.html", parameters)

# ================================== MY JOBS ===============================================

@login_required(login_url='login')
def my_applications(request):
    
    student = Student.objects.get(id=request.user.id)
    applications_list = Application.objects.filter(student=student).order_by('-application_date')
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(applications_list, 8)  # Show 8 applications per page
    
    try:
        applications = paginator.page(page)
    except PageNotAnInteger:
        applications = paginator.page(1)
    except EmptyPage:
        applications = paginator.page(paginator.num_pages)
    
    parameters = {
        "student": student,
        "applications": applications
    }
    
    return render(request, 'student/my_applications.html', parameters)

# ================================== JOB DETAILS ===========================================

@login_required(login_url='login')
def job(request, slug):
    try:
        job = Job.objects.select_related('company').get(slug=slug)
        student = Student.objects.get(id=request.user.id)
        
        # Check if student has complete profile
        if not all([student.tenth, student.twelfth, student.cgpa]):
            messages.error(request, "Complete your Profile to see eligible jobs for you")
            return redirect('my_profile')
        
        # Check eligibility
        is_eligible = (
            job.tenth_percentage <= student.tenth and
            job.twelfth_percentage <= student.twelfth and
            job.cgpa_criteria <= student.cgpa
        )
        
        # Check backlog restriction
        if student.backlog and student.backlog > 0 and not job.is_backlog_allowed:
            is_eligible = False
            messages.error(request, "This job does not allow students with backlogs.")
            return redirect('student')
        
        # Check interview date conflicts
        has_date_conflict = Application.objects.filter(
            student=student,
            job__interview_date=job.interview_date
        ).exists()
        
        if has_date_conflict:
            messages.error(request, "You have already applied to a company with the same interview date!")
            return redirect('student')
        
        # Check if student has already applied
        has_applied = Application.objects.filter(student=student, job=job).exists()
        
        parameters = {
            "student": student,
            "job": job,
            "is_eligible": is_eligible,
            "has_applied": has_applied
        }
        
        return render(request, 'student/job.html', parameters)
        
    except Job.DoesNotExist:
        messages.error(request, "Job not found.")
        return redirect('all_jobs')
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found. Please contact support.")
        return redirect('login')
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in job view: {str(e)}")
        messages.error(request, "An error occurred while loading the job details. Please try again later.")
        return redirect('all_jobs')

# ================================== APPLIED JOB ===========================================

@login_required(login_url='login')
def applied_job(request, slug):
        
    job = Job.objects.get(slug=slug)
    student = Student.objects.get(id=request.user.id)
    
    application = Application.objects.get(student=student, job=job)
    
    parameters = {
        "student": student,
        "job": job,
        "application": application
    }
    
    return render(request, 'student/applied_job.html', parameters)

# ================================== UPLOAD RESUME ===========================================

@login_required(login_url='login')
def upload_resume(request):
    
    student = Student.objects.get(id=request.user.id)
    
    if request.method == "POST":
        try:
            resume = request.FILES.get('resume')
            tenth_marksheet = request.FILES.get('tenth_marksheet')
            twelfth_marksheet = request.FILES.get('twelfth_marksheet')
            college_profile_print = request.FILES.get('college_profile_print')
            
            # Check if at least one file was uploaded
            if not any([resume, tenth_marksheet, twelfth_marksheet, college_profile_print]):
                messages.error(request, "Please select at least one file to upload.")
                return redirect('upload_resume')
            
            # Check file sizes (max 5MB) and file types
            max_size = 5 * 1024 * 1024  # 5MB in bytes
            for file_obj in [f for f in [resume, tenth_marksheet, twelfth_marksheet, college_profile_print] if f]:
                if file_obj.size > max_size:
                    messages.error(request, f"File '{file_obj.name}' is too large. Maximum size is 5MB.")
                    return redirect('upload_resume')
                
                # Check if file is PDF
                if not file_obj.name.lower().endswith('.pdf') and not file_obj.content_type == 'application/pdf':
                    messages.error(request, f"File '{file_obj.name}' is not a PDF. Only PDF files are allowed.")
                    return redirect('upload_resume')
            
            # Get the student and update fields
            student = Student.objects.get(id=request.user.id)            
            
            upload_success = False
            
            if resume:
                student.resume = resume
                upload_success = True
                
            if tenth_marksheet:
                student.tenth_marksheet = tenth_marksheet
                upload_success = True
                
            if twelfth_marksheet:
                student.twelfth_marksheet = twelfth_marksheet
                upload_success = True
                
            if college_profile_print:
                student.college_profile_print = college_profile_print
                upload_success = True
                
            student.save()
            
            # List of successfully uploaded files for the success message
            uploaded_files = []
            if resume:
                uploaded_files.append("Resume")
            if tenth_marksheet:
                uploaded_files.append("10th Marksheet")
            if twelfth_marksheet:
                uploaded_files.append("12th Marksheet")
            if college_profile_print:
                uploaded_files.append("College Profile")
            
            if uploaded_files:
                messages.success(request, f"Successfully uploaded: {', '.join(uploaded_files)}")
            else:
                messages.info(request, "No new documents were uploaded.")
                
            return redirect('upload_resume')
            
        except Exception as e:
            messages.error(request, f"Error uploading files: {str(e)}")
            return redirect('upload_resume')
    
    parameters = {
        "student": student
    }
    
    return render(request, 'student/upload_resume.html', parameters)

# ================================== ALL COMPANIES ===========================================

@login_required(login_url='login')
def all_jobs(request):
    
    student = Student.objects.get(id=request.user.id)
    jobs_list = Job.objects.all().exclude(applications__student=student)
    # for application in Application.objects.filter(student=student):
    #     jobs = jobs.exclude(interview_date=application.job.interview_date)
    if student.backlog:
        if student.backlog > 0:
            jobs_list = jobs_list.exclude(is_backlog_allowed=False)    
            
    query = request.GET.get("query")
    if query:
        # fetch the companies based on the name of the company, job role and descritiption
        jobs_list = Job.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(company__name__icontains=query)
        ).exclude(applications__student=student)
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(jobs_list, 12)  # Show 12 jobs per page
    
    try:
        jobs = paginator.page(page)
    except PageNotAnInteger:
        jobs = paginator.page(1)
    except EmptyPage:
        jobs = paginator.page(paginator.num_pages)
    
    parameters = {
        "student": student,
        "jobs": jobs,
        "query": query
    }
    
    return render(request, 'student/all_jobs.html', parameters)

# ================================== CONFIRM APPLICATION ===========================================

@login_required(login_url='login')
def confirm_application(request, slug):
    
    job = Job.objects.get(slug=slug)
    student = Student.objects.get(id=request.user.id)
    
    if student.no_of_companies_left > 0:
        parameters = {
            "student": student,
            "job": job
        }
        return render(request, 'student/confirmation.html', parameters)
    
    else:
        messages.error(request, "You have already applied to 3 companies!")
        return redirect('student')
    
# ================================== APPLY ===========================================

@login_required(login_url='login')
def apply(request, slug):
    
    job = Job.objects.get(slug=slug)
    student = Student.objects.get(id=request.user.id)
    
    eligible_jobs = Job.objects.filter(
        tenth_percentage__lte=student.tenth,
        twelfth_percentage__lte=student.twelfth,
        cgpa_criteria__lte=student.cgpa
    )
    
    # check if the user is eligible or not
    
    if job not in eligible_jobs:
        messages.error(request, "Sorry! You are not eligible for this job")
        return redirect('student')
    
    for application in Application.objects.filter(student=student):
        if application.job.interview_date == job.interview_date:
            messages.error(request, "You have already applied to a company which is coming on the same date!")
            return redirect('student')
        
    # check for the deadline of the job
    
    if job.deadline < datetime.now().date():
        messages.error(request, "The deadline for this job has been passed!")
        return redirect('student')
    
    if student.no_of_companies_left > 0:
        application = Application.objects.create(
            student=student,
            job=job
        )
        

        student.no_of_companies_left -= 1

        myfile=f"""
Dear {student.first_name} {student.last_name},

We are delighted to extend our warm greetings from the Department of Alumni Affairs at GLA University, Mathura.

We are pleased to inform you that your application for the position of {job.title.title()} at {job.company.name.title()}, submitted through GLANCE, the Mega Student Job Fair, has been successfully received. Congratulations on this significant step towards your career aspirations!

Below are the essential details regarding the upcoming interview:

Interview Date: {job.interview_date}
Interview Mode: {job.interview_mode}

If you wish to withdraw your application, 
- Go to the GLANCE portal
- Click on the 'My Applications' tab
- Select the Application you wish to withdraw
- Click on the 'Withdraw' button

Should you have any inquiries or require further assistance, please do not hesitate to contact us at alumniassociation01@gla.ac.in.

Best Regards,
Technical Team
Department of Alumni Affairs
GLA University, Mathura
"""

        email_subject = f"Application Confirmation: {job.title.title()} at GLANCE"
        email_body = myfile
        email_from = 'GLANCE JOB FAIR 2k24 <alumniassociation01@gla.ac.in>'
        email_to = [student.username]

        try:
            # Send the email
            send_mail(
                email_subject, 
                email_body, 
                email_from, 
                email_to,
                fail_silently=False
                )
        
        except Exception as e:
            print(f"Error sending email: {e}")
            messages.warning(request, "You will get the confirmation mail soon!")
        
        student.save()
        application.save()
        
        messages.success(request, "Application submitted successfully")
        return redirect('student')
    
    else:
        messages.error(request, "You have already applied to 3 companies!")
        return redirect('student')

# ================================== WITHDRAW APPLICATION ===========================================

@login_required(login_url='login')
def withdraw_application(request, slug):
    try:
        job = Job.objects.get(slug=slug)
        student = Student.objects.get(id=request.user.id)
        
        try:
            application = Application.objects.get(student=student, job=job)
            
            # Only allow withdrawal if application is still pending
            if application.status == 'pending':
                application.delete()
                student.no_of_companies_left += 1
                student.save()
                
                myfile = f"""
Dear {student.first_name} {student.last_name},

We trust this email finds you in good health and high spirits.

It is with regret that we inform you of the withdrawal of your application for the position of {job.title.title()} at {job.company.name.title()} for the GLANCE Mega Job Fair, as per your request.

Should you feel that this was a mistake or wish to reapply,
- Go to the GLANCE portal
- Click on the 'All Companies' tab
- Find the company you wish to apply to
- Click on the 'Apply' button

For any further inquiries or if you require assistance, please do not hesitate to contact us at alumniassociation01@gla.ac.in.

Best regards,

Technical Team
Department of Alumni Affairs,
GLA University, Mathura"""

                email_subject = f"Application Withdrawn: {job.title.title()} at GLANCE"
                email_body = myfile
                email_from = 'GLANCE JOB FAIR 2k24 <alumniassociation01@gla.ac.in>'
                email_to = [student.username]

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
                    messages.warning(request, "You'll get the confirmation mail soon!")
                
                messages.success(request, "Application withdrawn successfully")
            else:
                messages.error(request, "Cannot withdraw application - it has already been processed")
                
        except Application.DoesNotExist:
            messages.error(request, "No active application found for this job")
            
    except Job.DoesNotExist:
        messages.error(request, "The job you're trying to withdraw from doesn't exist")
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found")
    except Exception as e:
        print(f"Error in withdraw_application: {e}")
        messages.error(request, "An error occurred while processing your request")
    
    return redirect('my_applications')

# ================================== NOTIFICATIONS ===========================================

@login_required(login_url='login')
def notifications(request):
    
    student = Student.objects.get(id=request.user.id)
    notifications = Notification.objects.all()[::-1]
    
    parameters = {
        "student": student,
        "notifications": notifications
    }
    
    return render(request, 'student/notifications.html', parameters)


# ================================== SUPPORT ===========================================

@login_required(login_url='login')
def support(request):
    
    student = Student.objects.get(id=request.user.id)
    
    parameters = {
        "student": student
    }
    
    return render(request, 'student/support.html', parameters)