from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.http import JsonResponse
from django.db.models import Q, F, Value, CharField
from django.db.models.functions import Concat
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.core.exceptions import PermissionDenied
from .models import Student, Application
import logging
import operator
from functools import reduce

logger = logging.getLogger(__name__)

@method_decorator(csrf_protect, name='dispatch')
@method_decorator(require_http_methods(["GET"]), name='dispatch')
class StudentsDataTablesView(View):
    """View for handling DataTables requests for Students with optimized queries."""
    
    def dispatch(self, request, *args, **kwargs):
        # Additional security check
        if not request.user.is_authenticated or not request.user.is_staff:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        try:
            # Add debug print to see if this view is being called
            print(f"StudentsDataTablesView called with params: {request.GET}")
            
            # Validate request parameters
            try:
                draw = int(request.GET.get('draw', 1))
                start = max(0, int(request.GET.get('start', 0)))
                length = min(100, int(request.GET.get('length', 10)))  # Limit max records
            except ValueError as e:
                print(f"Parameter validation error: {e}")
                return JsonResponse({'error': f'Invalid parameters: {str(e)}'}, status=400)
                
            # Return a minimal working response for debugging
            if request.GET.get('limit', '') == '1':
                return JsonResponse({
                    'draw': 1,
                    'recordsTotal': 1,
                    'recordsFiltered': 1,
                    'data': [{'id': 1, 'first_name': 'Test', 'last_name': 'User'}]
                })
            
            # Log all request parameters for debugging
            logger.debug(f"DataTables API request: {request.GET}")
            
            # Base queryset with optimized field selection and annotations
            queryset = Student.objects.select_related('user_ptr').annotate(
                full_name=Concat('first_name', Value(' '), 'last_name', output_field=CharField())
            )
            
            # Apply filters with input sanitization
            filters = []
            
            # ID filter with validation
            id_filter = request.GET.get('id')
            if id_filter and id_filter.isdigit():
                filters.append(Q(id=int(id_filter)))
            
            # Name filter with sanitization
            name_filter = request.GET.get('name', '').strip()[:50]  # Limit length
            if name_filter:
                filters.append(
                    Q(first_name__icontains=name_filter) |
                    Q(last_name__icontains=name_filter)
                )
            
            # Email filter with validation
            email_filter = request.GET.get('email', '').strip()[:254]  # RFC 5321
            if email_filter:
                filters.append(Q(username__icontains=email_filter))
            
            # Phone filter with sanitization
            phone_filter = ''.join(filter(str.isdigit, request.GET.get('phone', '')))[:12]
            if phone_filter:
                filters.append(Q(phone_number__icontains=phone_filter))
            
            # Course and Year filters with validation
            course_filters = request.GET.getlist('course[]')  # Get all selected courses
            if course_filters:
                course_query = Q()
                for course in course_filters:
                    course = course.strip()[:100]  # Sanitize and limit length
                    if course:
                        course_query |= Q(course__icontains=course)
                if course_query:
                    filters.append(course_query)
                    logger.debug(f"Applied course filters: {course_filters}")
            
            year_filter = request.GET.get('year', '').strip()[:15]
            if year_filter and year_filter != 'all':
                filters.append(Q(year=year_filter))
            
            # CGPA filter with validation
            cgpa_filter = request.GET.get('cgpa')
            cgpa_operator = request.GET.get('cgpa_operator')
            if cgpa_filter and cgpa_operator in ['>', '<', '>=', '<=', '=']:
                try:
                    cgpa_value = float(cgpa_filter)
                    if 0 <= cgpa_value <= 10:  # Valid CGPA range
                        cgpa_filter_map = {
                            '>': 'cgpa__gt',
                            '<': 'cgpa__lt',
                            '>=': 'cgpa__gte',
                            '<=': 'cgpa__lte',
                            '=': 'cgpa'
                        }
                        filters.append(Q(**{cgpa_filter_map[cgpa_operator]: cgpa_value}))
                except ValueError:
                    pass
            
            # Status filter
            status_filter = request.GET.get('status', '').strip()[:20]
            if status_filter:
                filters.append(Q(alumni_status=status_filter))
            
            # Companies left filter
            companies_left = request.GET.get('companies_left')
            companies_operator = request.GET.get('companies_operator')
            if companies_left and companies_left.strip() and companies_operator in ['>', '<', '>=', '<=', '=']:
                try:
                    companies_value = int(companies_left)
                    companies_filter_map = {
                        '>': 'no_of_companies_left__gt',
                        '<': 'no_of_companies_left__lt',
                        '>=': 'no_of_companies_left__gte',
                        '<=': 'no_of_companies_left__lte',
                        '=': 'no_of_companies_left'
                    }
                    filters.append(Q(**{companies_filter_map[companies_operator]: companies_value}))
                    logger.debug(f"Applied companies_left filter: {companies_operator}{companies_value}")
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid companies_left value: {companies_left}, error: {e}")
            
            # Company filter
            company_filter = request.GET.get('company', '').strip()
            if company_filter:
                # Get student IDs who applied to the specified company
                company_students = Application.objects.filter(
                    job__company__name__icontains=company_filter
                ).values_list('student_id', flat=True).distinct()
                if company_students:
                    filters.append(Q(id__in=company_students))
                    logger.debug(f"Applied company filter: {company_filter}, matching students: {len(company_students)}")
                else:
                    # If no students match, add an impossible condition to return empty results
                    filters.append(Q(id=-1))
                    logger.debug(f"Applied company filter with no matches: {company_filter}")
            
            # Job filter
            job_filter = request.GET.get('job', '').strip()
            if job_filter:
                # Get student IDs who applied to the specified job
                job_students = Application.objects.filter(
                    job__title__icontains=job_filter
                ).values_list('student_id', flat=True).distinct()
                if job_students:
                    filters.append(Q(id__in=job_students))
                    logger.debug(f"Applied job filter: {job_filter}, matching students: {len(job_students)}")
                else:
                    # If no students match, add an impossible condition to return empty results
                    filters.append(Q(id=-1))
                    logger.debug(f"Applied job filter with no matches: {job_filter}")
            
            # Attendance status filter
            attendance_status = request.GET.get('attendance_status', '').strip()
            if attendance_status:
                if attendance_status == 'present':
                    # Get student IDs who are marked present
                    present_students = Application.objects.filter(
                        attendance__is_present=True
                    ).values_list('student_id', flat=True).distinct()
                    if present_students:
                        filters.append(Q(id__in=present_students))
                        logger.debug(f"Applied attendance filter: present, matching students: {len(present_students)}")
                    else:
                        # If no students match, add an impossible condition to return empty results
                        filters.append(Q(id=-1))
                        logger.debug("Applied attendance filter with no matches: present")
                elif attendance_status == 'absent':
                    # Get student IDs who are marked absent
                    absent_students = Application.objects.filter(
                        attendance__is_present=False
                    ).values_list('student_id', flat=True).distinct()
                    if absent_students:
                        filters.append(Q(id__in=absent_students))
                        logger.debug(f"Applied attendance filter: absent, matching students: {len(absent_students)}")
                    else:
                        # If no students match, add an impossible condition to return empty results
                        filters.append(Q(id=-1))
                        logger.debug("Applied attendance filter with no matches: absent")
                elif attendance_status == 'not_marked':
                    # Get student IDs who have applications but no attendance record
                    application_student_ids = Application.objects.values_list('student_id', flat=True).distinct()
                    attendance_student_ids = Application.objects.filter(
                        attendance__isnull=False
                    ).values_list('student_id', flat=True).distinct()
                    not_marked_student_ids = set(application_student_ids) - set(attendance_student_ids)
                    if not_marked_student_ids:
                        filters.append(Q(id__in=not_marked_student_ids))
                        logger.debug(f"Applied attendance filter: not marked, matching students: {len(not_marked_student_ids)}")
                    else:
                        # If no students match, add an impossible condition to return empty results
                        filters.append(Q(id=-1))
                        logger.debug("Applied attendance filter with no matches: not marked")
            
            # Log filters for debugging
            logger.debug(f"Applied filters: {filters}")
            
            # Apply all filters
            if filters:
                queryset = queryset.filter(reduce(operator.and_, filters))
            
            # Get total and filtered record counts
            total_records = Student.objects.count()
            filtered_records = queryset.count()
            
            logger.debug(f"Total records: {total_records}, Filtered records: {filtered_records}")
            
            # Apply pagination with limits
            paginator = Paginator(queryset, length)
            page_number = (start // length) + 1
            page_obj = paginator.get_page(page_number)
            
            # Prepare data with sanitized output
            data = []
            for student in page_obj:
                profile_score = min(100, max(0, student.get_profile_score()))  # Ensure valid range
                
                # Determine attendance status
                attendance_status = None
                try:
                    # Get most recent attendance for this student
                    attendance = Application.objects.filter(
                        student_id=student.id,
                        attendance__isnull=False
                    ).select_related('attendance').order_by('-attendance__marked_at').first()
                    
                    if attendance:
                        attendance_status = 'present' if attendance.attendance.is_present else 'absent'
                    else:
                        has_application = Application.objects.filter(student_id=student.id).exists()
                        if has_application:
                            attendance_status = 'not_marked'
                except Exception as e:
                    logger.error(f"Error getting attendance for student {student.id}: {str(e)}")
                
                student_data = {
                    'id': student.id,
                    'first_name': student.first_name[:50],  # Limit length
                    'last_name': student.last_name[:50],
                    'username': student.username[:254],
                    'phone_number': student.phone_number[:12],
                    'course': student.course[:100] if student.course else '',
                    'year': student.year[:15] if student.year else '',
                    'cgpa': float(student.cgpa) if student.cgpa else None,
                    'alumni_status': student.alumni_status[:20],
                    'no_of_companies_left': max(0, student.no_of_companies_left),  # Ensure non-negative
                    'profile_score': profile_score,
                    'attendance_status': attendance_status,
                    'actions': f'''
                        <div class="btn-group" role="group">
                            <a href="/student/profile/{student.id}" class="btn btn-sm btn-info">
                                <i class="fas fa-eye"></i> View
                            </a>
                            <button class="btn btn-sm btn-warning" onclick="editStudent({student.id})">
                                <i class="fas fa-edit"></i> Edit
                            </button>
                        </div>
                    '''
                }
                data.append(student_data)
            
            return JsonResponse({
                'draw': draw,
                'recordsTotal': total_records,
                'recordsFiltered': filtered_records,
                'data': data
            })
            
        except Exception as e:
            logger.error(f"Error in Students DataTables API: {str(e)}", exc_info=True)
            return JsonResponse({
                'error': 'Internal server error'
            }, status=500) 