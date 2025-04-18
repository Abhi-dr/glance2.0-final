from django.shortcuts import render, redirect, get_object_or_404
from accounts.models import Student, Company, Job, Application, Notification
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from datetime import datetime, date
from django.db.models import Q
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import Http404

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
def job_details(request, slug):
    student = Student.objects.get(id=request.user.id)
    job = get_object_or_404(Job, slug=slug)
    
    # Check if already applied
    has_applied = Application.objects.filter(student=student, job=job).exists()
    
    # Check eligibility
    is_eligible, eligibility_message = check_eligibility(student, job)
    
    # Format job salary range for better display - use simple string formatting instead
    salary_parts = job.salary_range.split('-') if job.salary_range and '-' in job.salary_range else None
    if salary_parts:
        try:
            # Format currency manually instead of using format_currency
            min_salary = f"₹{float(salary_parts[0].strip()):,.2f}"
            max_salary = f"₹{float(salary_parts[1].strip()):,.2f}"
            formatted_salary = f"{min_salary} - {max_salary}"
        except:
            formatted_salary = job.salary_range
    else:
        formatted_salary = job.salary_range
    
    parameters = {
        "student": student,
        "job": job,
        "is_eligible": is_eligible,
        "has_applied": has_applied,
        "eligibility_message": eligibility_message,
        "formatted_salary": formatted_salary,
        "today_date": date.today()
    }
    
    return render(request, 'student/job_details.html', parameters)

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
            
            # Get the student and update fields (student already fetched above)
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
    
    # Apply backlog restrictions
    if student.backlog and student.backlog > 0:
        jobs_list = jobs_list.exclude(is_backlog_allowed=False)    
            
    query = request.GET.get("query")
    if query:
        # fetch the companies based on the name of the company, job role and descritiption
        jobs_list = Job.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(company__name__icontains=query)
        ).exclude(applications__student=student)
        
        # Re-apply backlog restrictions on search results
        if student.backlog and student.backlog > 0:
            jobs_list = jobs_list.exclude(is_backlog_allowed=False)
    
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
def apply_job(request, slug):
    # Check if the student has companies_left
    student = Student.objects.get(id=request.user.id)
    
    if student.no_of_companies_left <= 0:
        messages.error(request, "You have already applied to the maximum number of companies.")
        return redirect('student')
    
    job = get_object_or_404(Job, slug=slug)
    
    # Check if the student has already applied for this job
    has_applied = Application.objects.filter(student=student, job=job).exists()
    
    if has_applied:
        messages.error(request, "You have already applied for this job.")
        return redirect('student')
    
    # Check eligibility
    is_eligible, eligibility_message = check_eligibility(student, job)
    
    if not is_eligible:
        messages.error(request, eligibility_message)
        return redirect('student')
        
    # Check interview date conflicts
    has_date_conflict = Application.objects.filter(
        student=student,
        job__interview_date=job.interview_date
    ).exists()
    
    if has_date_conflict:
        messages.error(request, "You have already applied to a company with the same interview date!")
        return redirect('student')
    
    # Create the application
    application = Application.objects.create(
        student=student,
        job=job,
        status='pending'
    )
        
    # Decrease the number of companies the student can apply to
    student.no_of_companies_left -= 1
    student.save()
        
    messages.success(request, "Successfully applied for the job. Good luck!")
    
    # Redirect to the student dashboard
    return redirect('student')

# ================================== WITHDRAW APPLICATION ===========================================

@login_required(login_url='login')
def withdraw_application(request, job_slug):
    try:
        # Get job by slug
        job = get_object_or_404(Job, slug=job_slug)
        student = Student.objects.get(id=request.user.id)
        
        # Check if application exists
        try:
            application = Application.objects.get(job=job, student=student)
            
            # Only allow withdrawal if application is still pending
            if application.status == 'pending':
                application.delete()
                student.no_of_companies_left += 1
                student.save()
                
                # Log successful withdrawal
                print(f"Application withdrawn successfully: Student {student.id} from Job {job.id} ({job.slug})")
                
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
            # Log the error with more details
            print(f"Application not found: Job {job.slug}, Student {student.id} combination not found")
            messages.error(request, "No active application found for this job")
    except Http404:
        print(f"Job not found: Invalid job slug '{job_slug}'")
        messages.error(request, "Job not found")
    except Exception as e:
        # Add detailed error logging
        import traceback
        print(f"Error in withdraw_application: {e}")
        print(traceback.format_exc())
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

def check_eligibility(student, job):
    """
    Check if a student is eligible for a job based on criteria like CGPA, 10th, 12th marks.
    """
    # Perform regular eligibility checks
    if job.cgpa_criteria:
        if not student.cgpa:
            return False, "Your CGPA is not provided but required for this job"
        if float(student.cgpa) < float(job.cgpa_criteria):
            return False, f"Your CGPA ({student.cgpa}) is below the required criterion ({job.cgpa_criteria})"
    
    if job.tenth_percentage:
        if not student.tenth:
            return False, "Your 10th percentage is not provided but required for this job"
        if float(student.tenth) < float(job.tenth_percentage):
            return False, f"Your 10th percentage ({student.tenth}) is below the required criterion ({job.tenth_percentage})"
    
    if job.twelfth_percentage:
        if not student.twelfth:
            return False, "Your 12th percentage is not provided but required for this job"
        if float(student.twelfth) < float(job.twelfth_percentage):
            return False, f"Your 12th percentage ({student.twelfth}) is below the required criterion ({job.twelfth_percentage})"
    
    if not job.is_backlog_allowed:
        if student.backlog is None:
            return False, "Your backlog information is not provided but required for this job"
        if student.backlog > 0:
            return False, "You have backlogs and this company does not allow backlogs"
    
    return True, "You are eligible for this job"

# ================================== WITHDRAW APPLICATION BY ID ===========================================

@login_required(login_url='login')
def withdraw_application_by_id(request, app_id):
    try:
        # Get application by ID and verify it belongs to current user
        application = get_object_or_404(Application, id=app_id)
        
        if application.student.id != request.user.id:
            messages.error(request, "You can only withdraw your own applications")
            return redirect('my_applications')
        
        # Store job information before deletion for email notification
        job = application.job
        student = request.user
        
        # Only allow withdrawal if application is still pending
        if application.status == 'pending':
            application.delete()
            student.no_of_companies_left += 1
            student.save()
            
            # Log successful withdrawal
            print(f"Application withdrawn successfully: Application ID {app_id}, Student {student.id}, Job {job.id}")
            
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
            
    except Http404:
        # Application not found
        print(f"Application not found: Invalid application ID '{app_id}'")
        messages.error(request, "Application not found")
    except Exception as e:
        # Add detailed error logging
        import traceback
        print(f"Error in withdraw_application_by_id: {e}")
        print(traceback.format_exc())
        messages.error(request, "An error occurred while processing your request")
    
    return redirect('my_applications')