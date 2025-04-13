from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Case, When, IntegerField, F
from django.http import HttpResponse
import csv
from accounts.models import Student, Application, Job, Company, Attendance, Volunteer
from django.db.models.functions import TruncDate
from datetime import datetime


# Helper function to check if user is a volunteer
def volunteer_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'volunteer'):
            messages.error(request, "You don't have permission to access this page.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required(login_url='login')
@volunteer_required
def volunteer_dashboard(request):
    """
    Dashboard view for volunteers showing key metrics and recent activity
    """
    # Get statistics
    total_applications = Application.objects.filter(status="accepted").count()
    total_attendance_marked = Attendance.objects.count()
    students_present = Attendance.objects.filter(is_present=True).count()
    attendance_pending = total_applications - total_attendance_marked
    
    # Get interviews by date
    interview_dates = {}
    for date_choice in Job._meta.get_field('interview_date').choices:
        count = Application.objects.filter(
            status="accepted", 
            job__interview_date=date_choice[0]
        ).count()
        if count > 0:
            interview_dates[date_choice[0]] = count
    
    # Get recent attendance records
    recent_attendance = Attendance.objects.select_related(
        'application__student', 
        'application__job__company'
    ).order_by('-marked_at')[:10]
    
    context = {
        'total_applications': total_applications,
        'total_attendance_marked': total_attendance_marked,
        'students_present': students_present,
        'attendance_pending': attendance_pending,
        'interview_dates': interview_dates,
        'recent_attendance': recent_attendance,
    }
    
    return render(request, 'volunteer/dashboard.html', context)


@login_required(login_url='login')
@volunteer_required
def volunteer_applications(request):
    """
    View to display and filter student applications for attendance marking
    """
    # Get filter parameters
    search_query = request.GET.get('search', '')
    selected_date = request.GET.get('date', '')
    selected_company = request.GET.get('company', '')
    attendance_filter = request.GET.get('attendance', '')
    
    # Base queryset - only get accepted applications
    applications = Application.objects.filter(status="accepted").select_related(
        'student', 
        'job__company'
    ).prefetch_related('attendance')
    
    # Apply filters
    if search_query:
        applications = applications.filter(
            Q(student__first_name__icontains=search_query) |
            Q(student__last_name__icontains=search_query) |
            Q(student__university_roll_no__icontains=search_query)
        )
    
    if selected_date:
        applications = applications.filter(job__interview_date=selected_date)
    
    if selected_company:
        applications = applications.filter(job__company__id=selected_company)
    
    if attendance_filter:
        if attendance_filter == 'marked':
            applications = applications.filter(attendance__isnull=False)
        elif attendance_filter == 'pending':
            applications = applications.filter(attendance__isnull=True)
        elif attendance_filter == 'present':
            applications = applications.filter(attendance__is_present=True)
        elif attendance_filter == 'absent':
            applications = applications.filter(attendance__is_present=False)
    
    # Get data for filter dropdowns
    interview_dates = []
    for date_choice in Job._meta.get_field('interview_date').choices:
        interview_dates.append(date_choice[0])
    
    companies = Company.objects.all()
    
    context = {
        'applications': applications,
        'interview_dates': interview_dates,
        'companies': companies,
        'selected_date': selected_date,
        'selected_company': selected_company,
        'attendance_filter': attendance_filter,
        'search_query': search_query,
    }
    
    return render(request, 'volunteer/applications.html', context)


@login_required(login_url='login')
@volunteer_required
def volunteer_applications_by_date(request, date):
    """
    View to display applications filtered by interview date
    """
    # Redirect to applications view with date filter
    return redirect(f'/volunteer/applications/?date={date}')


@login_required(login_url='login')
@volunteer_required
def volunteer_attendance(request):
    """
    View to display and filter attendance records
    """
    # Get filter parameters
    search_query = request.GET.get('search', '')
    selected_date = request.GET.get('date', '')
    selected_company = request.GET.get('company', '')
    status_filter = request.GET.get('status', '')
    
    # Base queryset
    attendance_records = Attendance.objects.select_related(
        'application__student',
        'application__job__company',
        'marked_by'
    ).order_by('-marked_at')
    
    # Apply filters
    if search_query:
        attendance_records = attendance_records.filter(
            Q(application__student__first_name__icontains=search_query) |
            Q(application__student__last_name__icontains=search_query) |
            Q(application__student__university_roll_no__icontains=search_query)
        )
    
    if selected_date:
        attendance_records = attendance_records.filter(application__job__interview_date=selected_date)
    
    if selected_company:
        attendance_records = attendance_records.filter(application__job__company__id=selected_company)
    
    if status_filter:
        is_present = True if status_filter == 'present' else False
        attendance_records = attendance_records.filter(is_present=is_present)
    
    # Get statistics
    present_count = attendance_records.filter(is_present=True).count()
    absent_count = attendance_records.filter(is_present=False).count()
    total_count = present_count + absent_count
    
    attendance_rate = 0
    if total_count > 0:
        attendance_rate = round((present_count / total_count) * 100)
    
    # Get data for filter dropdowns
    interview_dates = []
    for date_choice in Job._meta.get_field('interview_date').choices:
        interview_dates.append(date_choice[0])
    
    companies = Company.objects.all()
    
    context = {
        'attendance_records': attendance_records,
        'present_count': present_count,
        'absent_count': absent_count,
        'attendance_rate': attendance_rate,
        'interview_dates': interview_dates,
        'companies': companies,
        'selected_date': selected_date,
        'selected_company': selected_company,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'volunteer/attendance.html', context)


@login_required(login_url='login')
@volunteer_required
def mark_attendance(request, application_id, status):
    """
    View to mark a student's attendance
    """
    application = get_object_or_404(Application, id=application_id)
    
    # Check if attendance already exists
    if hasattr(application, 'attendance'):
        messages.warning(request, f"Attendance for {application.student.first_name} {application.student.last_name} has already been marked.")
        return redirect('volunteer_applications')
    
    is_present = status == 'present'
    
    # Create attendance record
    attendance = Attendance.objects.create(
        application=application,
        is_present=is_present,
        marked_by=request.user.volunteer
    )
    
    status_text = "present" if is_present else "absent"
    messages.success(request, f"Marked {application.student.first_name} {application.student.last_name} as {status_text}.")
    
    # Redirect to the referring page or applications page
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    else:
        return redirect('volunteer_applications')


@login_required(login_url='login')
@volunteer_required
def change_attendance(request, attendance_id):
    """
    View to change a student's attendance status
    """
    attendance = get_object_or_404(Attendance, id=attendance_id)
    
    # Toggle attendance status
    attendance.is_present = not attendance.is_present
    attendance.marked_by = request.user.volunteer
    attendance.marked_at = datetime.now()
    attendance.save()
    
    status_text = "present" if attendance.is_present else "absent"
    messages.success(request, f"Updated {attendance.application.student.first_name} {attendance.application.student.last_name}'s attendance to {status_text}.")
    
    # Redirect to the referring page or attendance page
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    else:
        return redirect('volunteer_attendance')


@login_required(login_url='login')
@volunteer_required
def export_attendance_csv(request):
    """
    View to export attendance records as CSV
    """
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance_records.csv"'
    
    # Create CSV writer
    writer = csv.writer(response)
    writer.writerow([
        'Student Name', 
        'University Roll No',
        'Course', 
        'Year', 
        'Company', 
        'Job Role', 
        'Interview Date',
        'Status',
        'Marked By',
        'Marked On'
    ])
    
    # Get all attendance records
    attendance_records = Attendance.objects.select_related(
        'application__student',
        'application__job__company',
        'marked_by'
    ).order_by('-marked_at')
    
    # Write data rows
    for record in attendance_records:
        writer.writerow([
            f"{record.application.student.first_name} {record.application.student.last_name}",
            record.application.student.university_roll_no,
            record.application.student.course,
            record.application.student.year,
            record.application.job.company.name,
            record.application.job.role,
            record.application.job.interview_date,
            "Present" if record.is_present else "Absent",
            f"{record.marked_by.first_name} {record.marked_by.last_name}",
            record.marked_at.strftime("%Y-%m-%d %H:%M:%S")
        ])
    
    return response 