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
    
    # Check if student has complete profile using helper function
    has_complete_profile, missing_items, _ = check_profile_completeness(student)
    
    try:
        # Only fetch jobs if student has complete profile
        if has_complete_profile:
            # Get today's date for comparison
            today = date.today()
            
            # Get active eligible jobs (non-expired) first
            active_eligible_jobs = []
            for job in Job.objects.filter(deadline__gte=today).order_by('deadline'):
                is_eligible, _ = check_eligibility(student, job)
                if is_eligible:
                    active_eligible_jobs.append(job)
            
            # Get expired eligible jobs
            expired_eligible_jobs = []
            for job in Job.objects.filter(deadline__lt=today).order_by('-deadline'):
                is_eligible, _ = check_eligibility(student, job)
                if is_eligible:
                    expired_eligible_jobs.append(job)
            
            # Combine active and expired jobs
            all_eligible_jobs = active_eligible_jobs + expired_eligible_jobs
            
            # Get first 3 jobs for dashboard display
            eligible_jobs = all_eligible_jobs[:3]
            
            # Count eligible companies
            eligible_companies_count = len(all_eligible_jobs)
            
        # Get latest applications
        applications = Application.objects.filter(student=student).order_by('-application_date')[:5]
    except Exception as e:
        # Just log the error and continue - don't fail the entire page
        print(f"Error in dashboard: {str(e)}")
    
    # Calculate application percentage (out of 100)
    companies_applied_percentage = (no_of_companies_applied / companies_count) * 100
    companies_applied_percentage = min(companies_applied_percentage, 100)  # Cap at 100%
    
    # Safely calculate profile score
    profile_score = student.get_profile_score()
    
    parameters = {
        "student": student,
        "has_complete_profile": has_complete_profile,
        "missing_items": missing_items if not has_complete_profile else [],
        "no_of_companies_applied": no_of_companies_applied,
        "eligible_jobs": eligible_jobs,
        "eligible_companies_count": eligible_companies_count,
        "applications": applications,
        "companies_applied_percentage": companies_applied_percentage,
        "profile_score": profile_score,
        "today_date": date.today()
    }
    
    return render(request, 'student/index.html', parameters)

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
            
            # Enhanced resume file validation with comprehensive device support
            try:
                # Get device info if available
                device_info = request.POST.get('device_info', 'Unknown device')
                print(f"Processing file upload from: {device_info}")
                
                if not resume:
                    messages.error(request, "Please select a resume file to upload.")
                    return redirect("upload_resume")
                
                # Check file size (max 5MB)
                max_size = 5 * 1024 * 1024  # 5MB in bytes
                if resume.size > max_size:
                    messages.error(request, "Resume file is too large. Maximum size is 5MB.")
                    return redirect("upload_resume")
                
                # Log file information for debugging
                print(f"Resume file: name={resume.name}, size={resume.size}, content_type={resume.content_type}")
                
                # Enhanced PDF detection with multiple checks for cross-device compatibility
                is_pdf = False
                
                # 1. Check file extension (most reliable across devices)
                if resume.name.lower().endswith('.pdf'):
                    is_pdf = True
                    print("PDF detected by file extension")
                    
                # 2. Check content type (can vary across devices)
                pdf_content_types = [
                    'application/pdf',
                    'application/x-pdf',
                    'application/acrobat',
                    'applications/vnd.pdf',
                    'text/pdf',
                    'text/x-pdf'
                ]
                
                if resume.content_type in pdf_content_types:
                    is_pdf = True
                    print(f"PDF detected by content type: {resume.content_type}")
                
                # 3. Additional check for iOS and older Android devices that may report content type incorrectly
                if 'iPhone' in device_info or 'iPad' in device_info or 'Android' in device_info:
                    # For these devices, prioritize file extension over content type
                    if resume.name.lower().endswith('.pdf'):
                        is_pdf = True
                        print("PDF detection override for mobile device")
                
                # Final PDF validation
                if not is_pdf:
                    messages.error(request, "Resume must be a PDF file. Please convert your document to PDF format.")
                    return redirect("upload_resume")
                    
            except Exception as e:
                # Log the error but provide a user-friendly message
                print(f"Error validating resume: {str(e)}")
                messages.error(request, "There was a problem with your resume file. Please ensure it's a valid PDF under 5MB.")
                return redirect("upload_resume")
                
            # Save the resume with error handling
            try:
                student.resume = resume
                student.save()
            except Exception as e:
                # Log the error for debugging
                print(f"Error saving resume: {str(e)}")
                # Provide a user-friendly error message
                messages.error(request, "There was a problem saving your resume. Please try again.")
                return redirect("upload_resume")
            
            upload_success = True
            
            # All other documents are optional - validate them with enhanced device compatibility
            if tenth_marksheet:
                try:
                    # Get device info
                    device_info = request.POST.get('device_info', 'Unknown device')
                    
                    # Check file size for tenth marksheet
                    max_size = 5 * 1024 * 1024  # 5MB in bytes
                    if tenth_marksheet.size > max_size:
                        messages.warning(request, "10th Marksheet is too large (max 5MB). It was not uploaded.")
                    else:
                        # Enhanced PDF detection with multiple checks
                        is_pdf = False
                        
                        # Check file extension
                        if tenth_marksheet.name.lower().endswith('.pdf'):
                            is_pdf = True
                        
                        # Check various content types
                        pdf_content_types = ['application/pdf', 'application/x-pdf', 'application/acrobat', 'applications/vnd.pdf']
                        if tenth_marksheet.content_type in pdf_content_types:
                            is_pdf = True
                        
                        # Special handling for mobile devices
                        if ('iPhone' in device_info or 'iPad' in device_info or 'Android' in device_info) and tenth_marksheet.name.lower().endswith('.pdf'):
                            is_pdf = True
                        
                        if not is_pdf:
                            messages.warning(request, "10th Marksheet must be a PDF file. It was not uploaded.")
                        else:
                            student.tenth_marksheet = tenth_marksheet
                            print(f"Successfully processed 10th marksheet: {tenth_marksheet.name}")
                except Exception as e:
                    print(f"Error with 10th marksheet: {str(e)}")
                    messages.warning(request, "There was an issue with your 10th Marksheet. It was not uploaded.")
                
            if twelfth_marksheet:
                try:
                    # Get device info
                    device_info = request.POST.get('device_info', 'Unknown device')
                    
                    # Check file size for twelfth marksheet
                    max_size = 5 * 1024 * 1024  # 5MB in bytes
                    if twelfth_marksheet.size > max_size:
                        messages.warning(request, "12th Marksheet is too large (max 5MB). It was not uploaded.")
                    else:
                        # Enhanced PDF detection with multiple checks
                        is_pdf = False
                        
                        # Check file extension
                        if twelfth_marksheet.name.lower().endswith('.pdf'):
                            is_pdf = True
                        
                        # Check various content types
                        pdf_content_types = ['application/pdf', 'application/x-pdf', 'application/acrobat', 'applications/vnd.pdf']
                        if twelfth_marksheet.content_type in pdf_content_types:
                            is_pdf = True
                        
                        # Special handling for mobile devices
                        if ('iPhone' in device_info or 'iPad' in device_info or 'Android' in device_info) and twelfth_marksheet.name.lower().endswith('.pdf'):
                            is_pdf = True
                        
                        if not is_pdf:
                            messages.warning(request, "12th Marksheet must be a PDF file. It was not uploaded.")
                        else:
                            student.twelfth_marksheet = twelfth_marksheet
                            print(f"Successfully processed 12th marksheet: {twelfth_marksheet.name}")
                except Exception as e:
                    print(f"Error with 12th marksheet: {str(e)}")
                    messages.warning(request, "There was an issue with your 12th Marksheet. It was not uploaded.")
                
            if college_profile_print:
                try:
                    # Get device info
                    device_info = request.POST.get('device_info', 'Unknown device')
                    
                    # Check file size for college profile
                    max_size = 5 * 1024 * 1024  # 5MB in bytes
                    if college_profile_print.size > max_size:
                        messages.warning(request, "College Profile is too large (max 5MB). It was not uploaded.")
                    else:
                        # Enhanced PDF detection with multiple checks
                        is_pdf = False
                        
                        # Check file extension
                        if college_profile_print.name.lower().endswith('.pdf'):
                            is_pdf = True
                        
                        # Check various content types
                        pdf_content_types = ['application/pdf', 'application/x-pdf', 'application/acrobat', 'applications/vnd.pdf']
                        if college_profile_print.content_type in pdf_content_types:
                            is_pdf = True
                        
                        # Special handling for mobile devices
                        if ('iPhone' in device_info or 'iPad' in device_info or 'Android' in device_info) and college_profile_print.name.lower().endswith('.pdf'):
                            is_pdf = True
                        
                        if not is_pdf:
                            messages.warning(request, "College Profile must be a PDF file. It was not uploaded.")
                        else:
                            student.college_profile_print = college_profile_print
                            print(f"Successfully processed college profile: {college_profile_print.name}")
                except Exception as e:
                    print(f"Error with college profile: {str(e)}")
                    messages.warning(request, "There was an issue with your College Profile. It was not uploaded.")
            
            student.save()
            
            # List of successfully uploaded files for the success message
            uploaded_files = []
            uploaded_files.append("Resume")  # Resume is always uploaded at this point
            
            if tenth_marksheet:
                uploaded_files.append("10th Marksheet")
            if twelfth_marksheet:
                uploaded_files.append("12th Marksheet")
            if college_profile_print:
                uploaded_files.append("College Profile Print")
                
            # Success message will always include Resume at minimum
            messages.success(request, f"Successfully uploaded: {', '.join(uploaded_files)}")
                
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
    # Get today's date for comparison
    today = date.today()
    
    # Get all jobs 
    all_jobs_query = Job.objects.all().exclude(applications__student=student)
    
    # Apply filters
    query = request.GET.get("query")
    job_type = request.GET.get("job_type")
    salary_min = request.GET.get("salary_min")
    location = request.GET.get("location")
    cgpa_max = request.GET.get("cgpa_max")
    show_expired = request.GET.get("show_expired") == "on"
    
    # Filter by search query
    if query:
        all_jobs_query = all_jobs_query.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(company__name__icontains=query) |
            Q(role__icontains=query)
        )
    
    # Filter by job type
    if job_type:
        all_jobs_query = all_jobs_query.filter(job_type=job_type)
    
    # Filter by salary minimum (simple text comparison)
    if salary_min:
        # This is a rough filter since salary is stored as text
        all_jobs_query = all_jobs_query.filter(salary_range__icontains=salary_min)
    
    # Filter by location
    if location:
        all_jobs_query = all_jobs_query.filter(location_flexibility__icontains=location)
    
    # Filter by maximum CGPA requirement
    if cgpa_max:
        try:
            cgpa_max_float = float(cgpa_max)
            all_jobs_query = all_jobs_query.filter(cgpa_criteria__lte=cgpa_max_float)
        except (ValueError, TypeError):
            pass  # Ignore invalid CGPA values
    
    # Apply backlog restrictions
    if student.backlog and student.backlog > 0:
        all_jobs_query = all_jobs_query.exclude(is_backlog_allowed=False)
    
    # Separate active and expired jobs
    if not show_expired:
        active_jobs = all_jobs_query.filter(deadline__gte=today).order_by('deadline')
        jobs_list = list(active_jobs)
    else:
        active_jobs = all_jobs_query.filter(deadline__gte=today).order_by('deadline')
        expired_jobs = all_jobs_query.filter(deadline__lt=today).order_by('-deadline')
        jobs_list = list(active_jobs) + list(expired_jobs)
    
    # Get unique job types for filter dropdown
    job_types = Job.objects.values_list('job_type', flat=True).distinct()
    
    # Get unique location options for filter dropdown
    locations = Job.objects.values_list('location_flexibility', flat=True).distinct()
    
    parameters = {
        "student": student,
        "jobs": jobs_list,
        "query": query,
        "job_type": job_type,
        "salary_min": salary_min,
        "location": location,
        "cgpa_max": cgpa_max,
        "show_expired": show_expired,
        "job_types": job_types,
        "locations": locations,
        "today_date": today,
        "total_jobs": len(jobs_list)
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
        messages.error(request, "You have already applied to 10 companies!")
        return redirect('student')
    
# ================================== APPLY ===========================================

@login_required(login_url='login')
def apply_job(request, slug):
    # Get the student
    student = Student.objects.get(id=request.user.id)
    
    # Only check if resume is uploaded (other documents are optional)
    if not student.resume:
        messages.error(request, "Please upload your resume before applying for jobs.")
        return redirect('upload_resume')
    
    # Check if the student has companies_left
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
    Check if a student is eligible for a job based on criteria.
    Returns a tuple of (is_eligible, message).
    """
    # If student has bypass_eligibility enabled, they're always eligible
    if student.bypass_eligibility:
        return True, "You are eligible for this job"
    
    # Handle missing fields gracefully - if a field is missing, we don't check that criterion
    
    # Check CGPA only if both job criteria and student CGPA are present
    if job.cgpa_criteria is not None and student.cgpa is not None:
        if student.cgpa < job.cgpa_criteria:
            return False, f"Your CGPA ({student.cgpa}) is lower than the required CGPA ({job.cgpa_criteria})"
    
    # Check 10th percentage only if both job criteria and student percentage are present
    if job.tenth_percentage is not None and student.tenth is not None:
        if student.tenth < job.tenth_percentage:
            return False, f"Your 10th percentage ({student.tenth}%) is lower than the required percentage ({job.tenth_percentage}%)"
    
    # Check 12th percentage only if both job criteria and student percentage are present
    if job.twelfth_percentage is not None and student.twelfth is not None:
        if student.twelfth < job.twelfth_percentage:
            return False, f"Your 12th percentage ({student.twelfth}%) is lower than the required percentage ({job.twelfth_percentage}%)"
    
    # Check backlog only if student backlog info is present
    if student.backlog is not None:
        if student.backlog > 0 and not job.is_backlog_allowed:
            return False, "This job does not allow students with backlogs"
    
    # If we get here, the student is eligible
    return True, "You are eligible for this job"

def check_profile_completeness(student):
    """
    Check if a student's profile is complete and has all required documents.
    Returns a tuple of (is_complete, missing_items, redirect_url).
    """
    missing_items = []
    
    # Check for resume (only mandatory document)
    if student.resume is None or not student.resume:
        return False, ["Resume"], 'upload_resume'
    
    # Make basic profile info optional
    optional_missing = []
    
    # These fields are now optional but we'll track them for informational purposes
    if student.tenth is None:
        optional_missing.append("10th percentage")
    if student.twelfth is None:
        optional_missing.append("12th percentage")
    if student.cgpa is None:
        optional_missing.append("CGPA")
    if student.gender is None:
        optional_missing.append("Gender")
    if student.course is None:
        optional_missing.append("Course")
    if student.year is None:
        optional_missing.append("Year")
    
    # Log optional missing items but don't prevent application
    if optional_missing:
        print(f"Student {student.id} is missing optional profile fields: {', '.join(optional_missing)}")
    
    # Other documents are optional, so we don't check for them here
    
    # Profile picture is optional, so we don't require it
    
    # All mandatory checks passed
    return True, [], None

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