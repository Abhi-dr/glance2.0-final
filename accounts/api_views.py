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
from .models import Student
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
            # Validate request parameters
            try:
                draw = int(request.GET.get('draw', 1))
                start = max(0, int(request.GET.get('start', 0)))
                length = min(100, int(request.GET.get('length', 10)))  # Limit max records
            except ValueError:
                return JsonResponse({'error': 'Invalid parameters'}, status=400)
            
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
                filters.append(Q(email__icontains=email_filter))
            
            # Phone filter with sanitization
            phone_filter = ''.join(filter(str.isdigit, request.GET.get('phone', '')))[:12]
            if phone_filter:
                filters.append(Q(phone_number__icontains=phone_filter))
            
            # Course and Year filters with validation
            course_filter = request.GET.get('course', '').strip()[:100]
            if course_filter:
                filters.append(Q(course=course_filter))
            
            year_filter = request.GET.get('year', '').strip()[:15]
            if year_filter:
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
            
            # Apply all filters
            if filters:
                queryset = queryset.filter(reduce(operator.and_, filters))
            
            # Get total and filtered record counts
            total_records = Student.objects.count()
            filtered_records = queryset.count()
            
            # Apply pagination with limits
            paginator = Paginator(queryset, length)
            page_number = (start // length) + 1
            page_obj = paginator.get_page(page_number)
            
            # Prepare data with sanitized output
            data = []
            for student in page_obj:
                profile_score = min(100, max(0, student.get_profile_score()))  # Ensure valid range
                student_data = {
                    'id': student.id,
                    'first_name': student.first_name[:50],  # Limit length
                    'last_name': student.last_name[:50],
                    'username': student.email[:254],
                    'phone_number': student.phone_number[:12],
                    'course': student.course[:100] if student.course else '',
                    'year': student.year[:15] if student.year else '',
                    'cgpa': float(student.cgpa) if student.cgpa else None,
                    'alumni_status': student.alumni_status[:20],
                    'no_of_companies_left': max(0, student.no_of_companies_left),  # Ensure non-negative
                    'profile_score': profile_score,
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