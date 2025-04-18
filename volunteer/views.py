from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Case, When, IntegerField, F, Sum
from django.http import HttpResponse
from django.contrib import messages
from accounts.models import Student, Application, Job, Company, Attendance, Volunteer
from django.db.models.functions import TruncDate
from datetime import datetime, timedelta
import csv
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.cache import cache
from django.utils import timezone


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
    # Try to get cached data first (cache for 5 minutes)
    cache_key = f'volunteer_dashboard_{request.user.id}'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return render(request, 'volunteer/dashboard.html', cached_data)
    
    # Get statistics with more efficient queries using Django's ORM capabilities
    total_applications = Application.objects.count()
    
    # Get attendance counts with a single query using annotate and Sum
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
    
    # Get recent attendance records with optimized select_related
    # Limit the fields to only those needed for display
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
    
    # Cache the dashboard data for 5 minutes
    cache.set(cache_key, context, 300)
    
    return render(request, 'volunteer/dashboard.html', context)


@login_required(login_url='login')
@volunteer_required
def volunteer_applications(request):
    """
    View to display and filter all student applications for attendance marking
    """
    # Get filter parameters
    search_query = request.GET.get('search', '').strip()
    selected_date = request.GET.get('date', '')
    selected_company = request.GET.get('company', '')
    attendance_filter = request.GET.get('attendance', '')
    status_filter = request.GET.get('status', '')
    
    # Base queryset with optimized select_related and prefetch_related
    applications = Application.objects.select_related(
        'student', 
        'job__company'
    ).prefetch_related('attendance').order_by('-application_date')
    
    # Apply filters
    if search_query:
        # Improved search functionality to handle partial matches better
        applications = applications.filter(
            Q(student__first_name__icontains=search_query) |
            Q(student__last_name__icontains=search_query) |
            Q(student__email__icontains=search_query) |
            Q(job__company__name__icontains=search_query) |
            Q(job__role__icontains=search_query)
        )
    
    if selected_date:
        applications = applications.filter(job__interview_date=selected_date)
    
    if selected_company:
        applications = applications.filter(job__company__id=selected_company)
    
    if status_filter:
        applications = applications.filter(status=status_filter)
        
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
    
    companies = Company.objects.all().order_by('name')
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(applications, 25)  # Show 25 applications per page
    
    try:
        applications_page = paginator.page(page)
    except PageNotAnInteger:
        applications_page = paginator.page(1)
    except EmptyPage:
        applications_page = paginator.page(paginator.num_pages)
    
    context = {
        'applications': applications_page,
        'total_count': paginator.count,
        'interview_dates': interview_dates,
        'companies': companies,
        'selected_date': selected_date,
        'selected_company': selected_company,
        'attendance_filter': attendance_filter,
        'status_filter': status_filter,
        'search_query': search_query,
        'now': timezone.now(),  # Add current time for the timestamp
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
            Q(application__student__email__icontains=search_query)
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
    # Check if this is an AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Fetch application with prefetched related objects to reduce queries
    application = get_object_or_404(
        Application.objects.select_related('student', 'job'),
        id=application_id
    )
    
    is_present = status == 'present'
    
    # Use Django's update_or_create to reduce database hits
    # This combines the check for existence and creation/update in a single query
    notes = None
    if application.status != "accepted":
        notes = f"Attendance marked while application was in {application.status} status."
    
    attendance, created = Attendance.objects.update_or_create(
        application=application,
        defaults={
            'is_present': is_present,
            'marked_by': request.user.volunteer,
            'marked_at': timezone.now(),
            'notes': notes
        }
    )
    
    # Clear dashboard cache
    cache_key = f'volunteer_dashboard_{request.user.id}'
    cache.delete(cache_key)
    
    # Prepare success message
    status_text = "present" if is_present else "absent"
    action_text = "Marked" if created else "Updated"
    messages.success(
        request, 
        f"{action_text} {application.student.first_name} {application.student.last_name}'s attendance to {status_text}."
    )
    
    # Handle AJAX requests differently
    if is_ajax:
        return HttpResponse(status=200)
    
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
    # Check if this is an AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Fetch attendance with prefetched related objects to reduce queries
    attendance = get_object_or_404(
        Attendance.objects.select_related('application__student'),
        id=attendance_id
    )
    
    # Toggle attendance status and update in a single query
    new_status = not attendance.is_present
    Attendance.objects.filter(id=attendance_id).update(
        is_present=new_status, 
        marked_by=request.user.volunteer.id,
        marked_at=timezone.now()
    )
    
    # Clear dashboard cache
    cache_key = f'volunteer_dashboard_{request.user.id}'
    cache.delete(cache_key)
    
    # Refresh the attendance object to get the updated values
    attendance.refresh_from_db()
    
    status_text = "present" if attendance.is_present else "absent"
    messages.success(
        request, 
        f"Updated {attendance.application.student.first_name} {attendance.application.student.last_name}'s attendance to {status_text}."
    )
    
    # Handle AJAX requests differently
    if is_ajax:
        return HttpResponse(status=200)
    
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


@login_required(login_url='login')
@volunteer_required
def bulk_mark_attendance(request):
    """
    View to mark attendance for multiple students at once
    """
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('volunteer_applications')
    
    # Check if this is an AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    application_ids = request.POST.getlist('application_ids', [])
    status = request.POST.get('status', 'present')
    is_present = status == 'present'
    
    if not application_ids:
        messages.error(request, "No applications selected.")
        return redirect('volunteer_applications') if not is_ajax else HttpResponse(status=400)
    
    # Get all selected applications in a single query with prefetch_related
    applications = Application.objects.filter(id__in=application_ids).select_related('student')
    
    # Use bulk update/create operations for better performance
    # First, check which applications already have attendance records
    existing_attendance_app_ids = Attendance.objects.filter(
        application_id__in=application_ids
    ).values_list('application_id', flat=True)
    
    current_time = timezone.now()
    
    # For applications with existing attendance, update them
    if existing_attendance_app_ids:
        Attendance.objects.filter(application_id__in=existing_attendance_app_ids).update(
            is_present=is_present,
            marked_by=request.user.volunteer,
            marked_at=current_time
        )
    
    # For applications without attendance records, create new ones
    new_attendance_apps = applications.exclude(id__in=existing_attendance_app_ids)
    attendance_objects = []
    
    for application in new_attendance_apps:
        notes = None
        if application.status != "accepted":
            notes = f"Attendance marked while application was in {application.status} status."
        
        attendance = Attendance(
            application=application,
            is_present=is_present,
            marked_by=request.user.volunteer,
            marked_at=current_time,
            notes=notes
        )
        attendance_objects.append(attendance)
    
    # Bulk create the new attendance records
    if attendance_objects:
        Attendance.objects.bulk_create(attendance_objects)
    
    # Clear dashboard cache
    cache_key = f'volunteer_dashboard_{request.user.id}'
    cache.delete(cache_key)
    
    # Count how many records were affected
    total_updated = len(existing_attendance_app_ids)
    total_created = len(attendance_objects)
    total_affected = total_updated + total_created
    
    status_text = "present" if is_present else "absent"
    action_text = f"Updated {total_updated} and marked {total_created} new students" if total_updated > 0 else f"Marked {total_created} students"
    
    messages.success(request, f"{action_text} as {status_text}.")
    
    # Handle AJAX requests differently
    if is_ajax:
        return HttpResponse(status=200)
    
    # Redirect to the referring page or applications page
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    else:
        return redirect('volunteer_applications') 