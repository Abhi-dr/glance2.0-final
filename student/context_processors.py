from accounts.models import Student
from datetime import datetime, timedelta



def user_context_processor(request):
    
    if request.path.startswith('/tera0mera1_dknaman/'):
        return {} 
    
    user_type = None
    user_object = None

    if request.user.is_authenticated:
        try:
            if hasattr(request.user, 'student'):
                user_type = 'student'
                user_object = request.user.student
            elif hasattr(request.user, 'instructor'):
                user_type = 'instructor'
                user_object = request.user.instructor
            elif hasattr(request.user, 'administrator'):
                user_type = 'administrator'
                user_object = request.user.administrator
        except (Student.DoesNotExist):
            pass

    return {
        'user_type': user_type,
        'user': user_object,
    }
