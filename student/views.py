from django.shortcuts import render, redirect
from accounts.models import Student, Company, Job, Application, Notification
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from datetime import datetime
from django.db.models import Q


@login_required(login_url='login')
def home(request):
    
    student = Student.objects.get(id=request.user.id)
    no_of_companies_applied = Application.objects.filter(student=student).count()
    
    no_of_companies_applied_in_percentage = no_of_companies_applied * 50
    
    # Companies ============
    
    companies_count = Job.objects.all().count()
    
    # Jobs =================
    
    all_eligible_jobs = Job.objects.filter(
        tenth_percentage__lte=student.tenth,
        twelfth_percentage__lte=student.twelfth,
        cgpa_criteria__lte=student.cgpa,
    ).exclude(applications__student=student)
    
    # exclude the jobs which the student has already applied on the same date
    
    for application in Application.objects.filter(student=student):
        all_eligible_jobs = all_eligible_jobs.exclude(interview_date=application.job.interview_date)

    eligible_companies_count = (all_eligible_jobs.count() / companies_count) * 100
    
    eligible_jobs = Job.objects.filter(
        tenth_percentage__lte=student.tenth,
        twelfth_percentage__lte=student.twelfth,
        cgpa_criteria__lte=student.cgpa,
    ).exclude(applications__student=student)
    
    for application in Application.objects.filter(student=student):
        eligible_jobs = eligible_jobs.exclude(interview_date=application.job.interview_date)
    
     # exclude the jobs which requres no backlog and if the student have backlogs
    
    if student.backlog > 0:
        all_eligible_jobs = all_eligible_jobs.exclude(is_backlog_allowed=False)
        eligible_jobs = eligible_jobs.exclude(is_backlog_allowed=False)
    
    applications = Application.objects.filter(student=student)
    
    parameters = {
        "student": student,
        'no_of_companies_applied': no_of_companies_applied,
        "eligible_jobs": eligible_jobs[:3],
        # 'companies': companies,
        'all_eligible_jobs': all_eligible_jobs,
        'no_of_companies_applied_in_percentage': no_of_companies_applied_in_percentage,
        "eligible_companies_count": int(eligible_companies_count),
        
        "applications": applications
    }
    
    return render(request, 'student/index.html', parameters)

# ================================== MY JOBS ===============================================

@login_required(login_url='login')
def my_applications(request):
    
    student = Student.objects.get(id=request.user.id)
    applications = Application.objects.filter(student=student)
    
    parameters = {
        "student": student,
        "applications": applications
    }
    
    return render(request, 'student/my_applications.html', parameters)

# ================================== JOB DETAILS ===========================================

@login_required(login_url='login')
def job(request, slug):
    
    job = Job.objects.get(slug=slug)
    student = Student.objects.get(id=request.user.id)
    
    eligible_jobs = Job.objects.filter(
        tenth_percentage__lte=student.tenth,
        twelfth_percentage__lte=student.twelfth,
        cgpa_criteria__lte=student.cgpa
    )
    

    
    parameters = {
        "student": student,
        "job": job,
    }
    
    if job in eligible_jobs:
        return render(request, 'student/job.html', parameters)

    else:
        messages.error(request, "Sorry! You are not eligible for this job")
        return redirect('student')

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
        resume = request.FILES.get('resume')
        tenth_marksheet = request.FILES.get('tenth_marksheet')
        twelfth_marksheet = request.FILES.get('twelfth_marksheet')
        college_profile_print = request.FILES.get('college_profile_print')
        
        
        student = Student.objects.get(id=request.user.id)            
        
        if resume:
            student.resume = resume
        if tenth_marksheet:
            student.tenth_marksheet = tenth_marksheet
        if twelfth_marksheet:
            student.twelfth_marksheet = twelfth_marksheet
        if college_profile_print:
            student.college_profile_print = college_profile_print
            
        student.save()
        
        messages.success(request, "Documents Uploaded successfully")
        return redirect('upload_resume')
    
    parameters = {
        "student": student
    }
    
    return render(request, 'student/upload_resume.html', parameters)

# ================================== ALL COMPANIES ===========================================

@login_required(login_url='login')
def all_jobs(request):
    
    student = Student.objects.get(id=request.user.id)
    jobs = Job.objects.all().exclude(applications__student=student)
    # for application in Application.objects.filter(student=student):
    #     jobs = jobs.exclude(interview_date=application.job.interview_date)
    
    if student.backlog > 0:
        jobs = jobs.exclude(is_backlog_allowed=False)    
        
    query = request.POST.get("query")
    print(query)
    if query:
        # fetch the companies based on the name of the company, job role and descritiption
        
        jobs = Job.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(company__name__icontains=query)
        ).exclude(applications__student=student)
    
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
        messages.error(request, "You have already applied to 2 companies!")
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

Should you have any inquiries or require further assistance, please do not hesitate to contact us at alumniassociation@gla.ac.in.

Best Regards,
Technical Team
Department of Alumni Affairs
GLA University, Mathura
"""

        email_subject = f"Application Confirmation: {job.title.title()} at GLANCE"
        email_body = myfile
        email_from = 'GLANCE JOB FAIR 2k24'
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
        
        except:
            messages.warning(request, "You will get the mail soon!")
        
        student.save()
        application.save()
        
        messages.success(request, "Application submitted successfully")
        return redirect('student')
    
    else:
        messages.error(request, "You have already applied to 2 companies!")
        return redirect('student')

# ================================== WITHDRAW APPLICATION ===========================================

@login_required(login_url='login')
def withdraw_application(request, slug):
    
    job = Job.objects.get(slug=slug)
    student = Student.objects.get(id=request.user.id)
    
    application = Application.objects.get(student=student, job=job)
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

For any further inquiries or if you require assistance, please do not hesitate to contact us at alumniassociation@gla.ac.in.

Best regards,

Technical Team
Department of Alumni Affairs,
GLA University, Mathura"""

    email_subject = f"Application Withdrawn: {job.title.title()} at GLANCE"
    email_body = myfile
    email_from = 'GLANCE JOB FAIR 2k24'
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
    except:
        messages.error(request, "You'll get the confirmation mail soon!")
        
    messages.success(request, "Application withdrawn successfully")
    return redirect('student')

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

# ================================== STUDENT PROFILE ===========================================

@login_required(login_url='login')
def my_profile(request):
    
    student = Student.objects.get(id=request.user.id)
    
    parameters = {
        "student": student
    }
    
    return render(request, 'student/my_profile.html', parameters)

# ================================== EDIT PROFILE ===========================================

@login_required(login_url='login')
def edit_profile(request):
    
    student = Student.objects.get(id=request.user.id)
    
    if request.method == "POST":
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        phone = request.POST['phone_number']
        gender = request.POST["gender"]
        
        linkedin_id = request.POST['linkedin_id']
        github_id = request.POST['github_id']
        
        student.first_name = first_name
        student.last_name = last_name
        student.phone = phone
        student.gender = gender
        student.linkedin_id = linkedin_id
        student.github_id = github_id
        
        student.save()
        
        messages.success(request, "Profile updated successfully")
        return redirect('my_profile')
    
    parameters = {
        "student": student
    }
    
    return render(request, 'student/edit_profile.html', parameters) 


# ================================== UPLOAD PROFILE ===========================================

@login_required(login_url='login')
def upload_profile(request):

    if request.method == 'POST':

        student = Student.objects.get(id=request.user.id)

        student.profile_pic = request.FILES['profile_pic']
        student.save()

        messages.success(request, 'Profile Picture Updated Successfully')

        return redirect('my_profile')
    
# ================================== SUPPORT ===========================================

@login_required(login_url='login')
def support(request):
    
    student = Student.objects.get(id=request.user.id)
    
    parameters = {
        "student": student
    }
    
    return render(request, 'student/support.html', parameters)