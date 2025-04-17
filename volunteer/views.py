from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Case, When, IntegerField, F
from django.http import HttpResponse
from django.contrib import messages
from accounts.models import Student, Application, Job, Company, Attendance, Volunteer
from django.db.models.functions import TruncDate
from datetime import datetime
import csv


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
    # Get statistics with more efficient queries
    total_applications = Application.objects.count()
    
    # Get attendance counts with a single query using annotate
    attendance_stats = Attendance.objects.aggregate(
        total=Count('id'),
        present=Count(Case(When(is_present=True, then=1), output_field=IntegerField())),
        absent=Count(Case(When(is_present=False, then=1), output_field=IntegerField()))
    )
    
    total_attendance_marked = attendance_stats['total']
    students_present = attendance_stats['present']
    students_absent = attendance_stats['absent']
    attendance_pending = total_applications - total_attendance_marked
    
    # Calculate attendance rate
    attendance_rate = 0
    if total_attendance_marked > 0:
        attendance_rate = round((students_present / total_attendance_marked) * 100)
    
    # Check if there's any data
    has_data = total_applications > 0
    
    # Get interviews by date - more efficient query using values and annotate
    interview_dates_data = Application.objects.values('job__interview_date').annotate(
        count=Count('id')
    ).order_by('job__interview_date')
    
    interview_dates = {}
    for item in interview_dates_data:
        if item['job__interview_date'] and item['count'] > 0:
            interview_dates[item['job__interview_date']] = item['count']
    
    # Get recent attendance records with select_related for efficiency
    recent_attendance = Attendance.objects.select_related(
        'application__student', 
        'application__job__company',
        'marked_by'
    ).order_by('-marked_at')[:10]
    
    context = {
        'total_applications': total_applications,
        'total_attendance_marked': total_attendance_marked,
        'students_present': students_present,
        'students_absent': students_absent,
        'attendance_rate': attendance_rate,
        'attendance_pending': attendance_pending,
        'interview_dates': interview_dates,
        'recent_attendance': recent_attendance,
        'has_data': has_data,
    }
    
    return render(request, 'volunteer/dashboard.html', context)


@login_required(login_url='login')
@volunteer_required
def volunteer_applications(request):
    """
    View to display and filter all student applications for attendance marking
    """
    # Add debug information
    print("="*50)
    print("volunteer_applications view called")
    print(f"Request GET parameters: {request.GET}")
    print("="*50)
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    selected_date = request.GET.get('date', '')
    selected_company = request.GET.get('company', '')
    attendance_filter = request.GET.get('attendance', '')
    status_filter = request.GET.get('status', '')
    
    print(f"Search query: '{search_query}'")
    print(f"Selected date: '{selected_date}'")
    print(f"Selected company: '{selected_company}'")
    print(f"Attendance filter: '{attendance_filter}'")
    print(f"Status filter: '{status_filter}'")
    
    # Base queryset - get all applications instead of just accepted ones
    applications = Application.objects.all().select_related(
        'student', 
        'job__company'
    ).prefetch_related('attendance')
    
    print(f"Initial application count: {applications.count()}")
    
    # Apply filters
    if search_query:
        applications = applications.filter(
            Q(student__first_name__icontains=search_query) |
            Q(student__last_name__icontains=search_query) |
            Q(student__university_roll_no__icontains=search_query)
        )
        print(f"After search query filter: {applications.count()} applications")
    
    if selected_date:
        applications = applications.filter(job__interview_date=selected_date)
        print(f"After date filter: {applications.count()} applications")
    
    if selected_company:
        applications = applications.filter(job__company__id=selected_company)
        print(f"After company filter: {applications.count()} applications")
    
    if status_filter:
        applications = applications.filter(status=status_filter)
        print(f"After status filter: {applications.count()} applications")
        
    if attendance_filter:
        if attendance_filter == 'marked':
            applications = applications.filter(attendance__isnull=False)
        elif attendance_filter == 'pending':
            applications = applications.filter(attendance__isnull=True)
        elif attendance_filter == 'present':
            applications = applications.filter(attendance__is_present=True)
        elif attendance_filter == 'absent':
            applications = applications.filter(attendance__is_present=False)
        print(f"After attendance filter: {applications.count()} applications")
    
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
        'status_filter': status_filter,
        'search_query': search_query,
    }
    
    print(f"Final application count: {applications.count()}")
    print("="*50)
    
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
    View to mark a student's attendance regardless of application status
    """
    application = get_object_or_404(Application, id=application_id)
    
    # Check if attendance already exists
    if hasattr(application, 'attendance'):
        # Update existing attendance
        attendance = application.attendance
        is_present = status == 'present'
        attendance.is_present = is_present
        attendance.marked_by = request.user.volunteer
        attendance.marked_at = datetime.now()
        attendance.save()
        
        status_text = "present" if is_present else "absent"
        messages.success(request, f"Updated {application.student.first_name} {application.student.last_name}'s attendance to {status_text}.")
    else:
        # Create new attendance record
        is_present = status == 'present'
        
        notes = None
        # Add a note if application is not accepted
        if application.status != "accepted":
            notes = f"Attendance marked while application was in {application.status} status."
        
        # Create attendance record
        attendance = Attendance.objects.create(
            application=application,
            is_present=is_present,
            marked_by=request.user.volunteer,
            notes=notes
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


@login_required(login_url='login')
@volunteer_required
def volunteer_profile(request):
    """
    View for displaying the volunteer's profile with activity statistics
    """
    volunteer = request.user.volunteer
    
    # Get attendance statistics
    from django.db.models import Count, Q
    from datetime import timedelta
    from django.utils import timezone
    
    # Count total attendance records marked by this volunteer
    attendance_count = Attendance.objects.filter(marked_by=volunteer).count()
    
    # Count unique days the volunteer has been active
    days_active = Attendance.objects.filter(marked_by=volunteer).dates('marked_at', 'day').count()
    
    # Count unique companies the volunteer has handled
    companies_count = Attendance.objects.filter(marked_by=volunteer).values(
        'application__job__company'
    ).distinct().count()
    
    context = {
        'volunteer': volunteer,
        'attendance_count': attendance_count,
        'days_active': days_active,
        'companies_count': companies_count,
    }
    
    return render(request, 'volunteer/profile.html', context) 